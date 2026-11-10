"""Hash refresh tokens at rest and add refresh token families.

This migration is written by hand, as the auto-generated version would be unsafe:

- The plaintext `token` column is kept (as `legacy_token`, same column) instead of being
  dropped, so existing tokens keep working, tokens issued by older versions during a rolling
  upgrade can still be found, and rolling back the image keeps working. A future release will
  clear and drop it.
- `family` is added without a default and backfilled with one UUID per row. Adding it with
  `default=uuid4` would put every existing token into the same family, so that any reuse would
  revoke all refresh tokens.
- The backfill is a single SQL statement instead of a Python loop, as this table can be large.
"""

import uuid

import django.contrib.postgres.indexes
from django.db import migrations, models

import authentik.lib.utils.time

BACKFILL = """
-- Expired tokens are deleted by `clean_expired_models` anyways, skip backfilling them
DELETE FROM authentik_providers_oauth2_refreshtoken WHERE expiring AND expires < now();
UPDATE authentik_providers_oauth2_refreshtoken
SET token_hash = encode(sha256(convert_to(token, 'UTF8')), 'hex'),
    family = gen_random_uuid()
WHERE token_hash IS NULL;
"""


class Migration(migrations.Migration):

    dependencies = [
        ("authentik_providers_oauth2", "0038_oauth2sessionlogin"),
    ]

    operations = [
        # Rename `token` to `legacy_token` without touching the column, and make it nullable
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.RemoveIndex(
                    model_name="refreshtoken",
                    name="authentik_p_token_32e2b7_hash",
                ),
                migrations.RenameField(
                    model_name="refreshtoken",
                    old_name="token",
                    new_name="legacy_token",
                ),
                migrations.AlterField(
                    model_name="refreshtoken",
                    name="legacy_token",
                    field=models.TextField(db_column="token", default=None, null=True),
                ),
                migrations.AddIndex(
                    model_name="refreshtoken",
                    index=django.contrib.postgres.indexes.HashIndex(
                        fields=["legacy_token"], name="authentik_p_token_32e2b7_hash"
                    ),
                ),
            ],
            database_operations=[
                migrations.AlterField(
                    model_name="refreshtoken",
                    name="token",
                    field=models.TextField(default=None, null=True),
                ),
            ],
        ),
        migrations.AddField(
            model_name="refreshtoken",
            name="token_hash",
            field=models.TextField(default=None, null=True),
        ),
        migrations.AddField(
            model_name="refreshtoken",
            name="family",
            field=models.UUIDField(default=None, null=True),
        ),
        migrations.AddField(
            model_name="refreshtoken",
            name="rotated_at",
            field=models.DateTimeField(default=None, null=True),
        ),
        # Access tokens are short-lived, existing ones are not backfilled and expire without a
        # family
        migrations.AddField(
            model_name="accesstoken",
            name="family",
            field=models.UUIDField(db_index=True, default=None, null=True),
        ),
        migrations.RunSQL(BACKFILL, reverse_sql=migrations.RunSQL.noop),
        # Create indexes after the backfill, which is faster than updating them row by row
        migrations.AlterField(
            model_name="refreshtoken",
            name="family",
            field=models.UUIDField(db_index=True, default=uuid.uuid4, null=True),
        ),
        migrations.AddIndex(
            model_name="refreshtoken",
            index=django.contrib.postgres.indexes.HashIndex(
                fields=["token_hash"], name="authentik_p_token_h_51a65d_hash"
            ),
        ),
        # Existing providers keep the previous behaviour (reuse is only logged), new providers
        # revoke the family on reuse
        migrations.AddField(
            model_name="oauth2provider",
            name="refresh_token_revoke_family_on_reuse",
            field=models.BooleanField(
                default=False,
                help_text=(
                    "When a refresh token which has already been rotated is used again, revoke "
                    "all refresh and access tokens issued from the same authorization. Reuse "
                    "indicates that the token may have been stolen."
                ),
            ),
        ),
        migrations.AlterField(
            model_name="oauth2provider",
            name="refresh_token_revoke_family_on_reuse",
            field=models.BooleanField(
                default=True,
                help_text=(
                    "When a refresh token which has already been rotated is used again, revoke "
                    "all refresh and access tokens issued from the same authorization. Reuse "
                    "indicates that the token may have been stolen."
                ),
            ),
        ),
        migrations.AddField(
            model_name="oauth2provider",
            name="refresh_token_reuse_grace_period",
            field=models.TextField(
                default="seconds=30",
                help_text=(
                    "Allow the most recently rotated refresh token to be used again for this "
                    "duration without revoking its family, for clients which retry or send "
                    "concurrent refresh requests. Only applies when revoking the family on reuse "
                    "is enabled. (Format: hours=1;minutes=2;seconds=3)."
                ),
                validators=[authentik.lib.utils.time.timedelta_string_validator],
            ),
        ),
    ]
