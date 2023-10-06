# flake8: noqa
from lifecycle.migrate import BaseMigration

SQL_STATEMENT = """
DELETE FROM django_migrations WHERE app = 'otp_static';
DELETE FROM django_migrations WHERE app = 'otp_totp';
-- Rename tables (static)
ALTER TABLE otp_static_staticdevice RENAME TO authentik_stages_authenticator_static_staticdevice;
ALTER TABLE otp_static_statictoken RENAME TO authentik_stages_authenticator_static_statictoken;
ALTER SEQUENCE otp_static_statictoken_id_seq RENAME TO authentik_stages_authenticator_static_statictoken_id_seq;
ALTER SEQUENCE otp_static_staticdevice_id_seq RENAME TO authentik_stages_authenticator_static_staticdevice_id_seq;
-- Rename tables (totp)
ALTER TABLE otp_totp_totpdevice RENAME TO authentik_stages_authenticator_totp_totpdevice;
ALTER SEQUENCE otp_totp_totpdevice_id_seq RENAME TO authentik_stages_authenticator_totp_totpdevice_id_seq;
"""


class Migration(BaseMigration):
    def needs_migration(self) -> bool:
        self.cur.execute(
            "select * from information_schema.tables WHERE table_name='otp_static_staticdevice'"
        )
        return bool(self.cur.rowcount)

    def run(self):
        with self.con.transaction():
            self.cur.execute(SQL_STATEMENT)
            self.fake_migration(
                (
                    "authentik_stages_authenticator_static",
                    "0008_initial",
                ),
                (
                    "authentik_stages_authenticator_static",
                    "0009_throttling",
                ),
                (
                    "authentik_stages_authenticator_totp",
                    "0008_initial",
                ),
                (
                    "authentik_stages_authenticator_totp",
                    "0009_auto_20190420_0723",
                ),
            )
