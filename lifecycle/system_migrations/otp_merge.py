# flake8: noqa
from lifecycle.migrate import BaseMigration

SQL_STATEMENT = """
BEGIN TRANSACTION;
-- Update migrations (static)
UPDATE django_migrations SET app = 'authentik_stages_authenticator_static', name = '0008_initial' WHERE app = 'otp_static' AND name = '0001_initial';
UPDATE django_migrations SET app = 'authentik_stages_authenticator_static', name = '0009_throttling' WHERE app = 'otp_static' AND name = '0002_throttling';
-- Rename tables (static)
ALTER TABLE otp_static_staticdevice RENAME TO authentik_stages_authenticator_static_staticdevice;
ALTER TABLE otp_static_statictoken RENAME TO authentik_stages_authenticator_static_statictoken;
ALTER SEQUENCE otp_static_statictoken_id_seq RENAME TO authentik_stages_authenticator_static_statictoken_id_seq;
ALTER SEQUENCE otp_static_staticdevice_id_seq RENAME TO authentik_stages_authenticator_static_staticdevice_id_seq;
-- Update migrations (totp)
UPDATE django_migrations SET app = 'authentik_stages_authenticator_totp', name = '0008_initial' WHERE app = 'otp_totp' AND name = '0001_initial';
UPDATE django_migrations SET app = 'authentik_stages_authenticator_totp', name = '0009_auto_20190420_0723' WHERE app = 'otp_totp' AND name = '0002_auto_20190420_0723';
-- Rename tables (totp)
ALTER TABLE otp_totp_totpdevice RENAME TO authentik_stages_authenticator_totp_totpdevice;
ALTER SEQUENCE otp_totp_totpdevice_id_seq RENAME TO authentik_stages_authenticator_totp_totpdevice_id_seq;
COMMIT;
"""


class Migration(BaseMigration):
    def needs_migration(self) -> bool:
        self.cur.execute(
            "select * from information_schema.tables WHERE table_name='otp_static_staticdevice'"
        )
        return bool(self.cur.rowcount)

    def run(self):
        self.cur.execute(
            "SELECT * FROM django_migrations WHERE app = 'authentik_stages_authenticator_static' AND name = '0007_authenticatorstaticstage_token_length_and_more';"
        )
        if not bool(self.cur.rowcount):
            raise Exception("Please upgrade to 2023.8 before upgrading to 2023.10")
        self.cur.execute(SQL_STATEMENT)
