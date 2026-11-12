"""Hash refresh tokens at rest and add refresh token families.

This migration is written by hand, as the auto-generated version would be unsafe:

- The plaintext `token` column is kept (as `legacy_token`, same column) instead of being
  dropped, so existing tokens keep working, tokens issued by older versions during a rolling
  upgrade can still be found, and rolling back the image keeps working. A future release will
  hash the remaining tokens, then clear and drop it.
- `family` is added without a default. Adding it with `default=uuid4` would put every existing
  token into the same family, so that any reuse would revoke all refresh tokens.

Existing tokens are deliberately not backfilled. This migration holds an exclusive lock on the
refresh token table, so instances still running the previous version can't refresh tokens
until it commits. In a local benchmark with 5M refresh tokens, a backfill (hashing every token
and assigning each a family) held that lock for 66s and wrote 20GB of WAL. Without it, only the
index builds remain. A backfill isn't needed either:

- Lookups fall back to the plaintext column, and `RefreshToken.save()` hashes an existing token
  the next time it is saved.
- A backfilled family would only ever contain the token itself, as previous versions didn't
  record which token was rotated from which. A family is started when an existing token is
  first refreshed instead.
- Expired tokens are deleted by `clean_expired_models`.
"""

import uuid

import django.contrib.postgres.indexes
from django.db import migrations, models

import authentik.lib.utils.time


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
        # Existing tokens have no family, only index the ones that do
        migrations.AddIndex(
            model_name="refreshtoken",
            index=models.Index(
                condition=models.Q(("family__isnull", False)),
                fields=["family"],
                name="authentik_p_rt_family_idx",
            ),
        ),
        # Only new tokens get a family by default, so this doesn't change existing rows
        migrations.AlterField(
            model_name="refreshtoken",
            name="family",
            field=models.UUIDField(default=uuid.uuid4, null=True),
        ),
        migrations.AddIndex(
            model_name="refreshtoken",
            index=django.contrib.postgres.indexes.HashIndex(
                fields=["token_hash"], name="authentik_p_token_h_51a65d_hash"
            ),
        ),
        # `token_hash` has no planner statistics yet. Without them, a lookup by token is
        # estimated to match many rows, and `.first()` (ORDER BY id LIMIT 1) is planned as a
        # walk of the primary key instead of an index lookup. In a local benchmark with 1M
        # refresh tokens, that made looking up a new or unknown token take ~250ms instead of
        # ~0.02ms until autovacuum analyzed the table. ANALYZE only samples the table, so it
        # is fast.
        migrations.RunSQL(
            "ANALYZE authentik_providers_oauth2_refreshtoken", reverse_sql=migrations.RunSQL.noop
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
