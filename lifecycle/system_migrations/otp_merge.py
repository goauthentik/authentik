# flake8: noqa
from os import system

from lifecycle.migrate import BaseMigration

SQL_STATEMENT = """
BEGIN TRANSACTION;
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
COMMIT;"""


class Migration(BaseMigration):
    def needs_migration(self) -> bool:
        self.cur.execute(
            "select * from information_schema.tables WHERE table_name='otp_static_staticdevice'"
        )
        return bool(self.cur.rowcount)

    def system_crit(self, command):
        retval = system(command)  # nosec
        if retval != 0:
            raise Exception("Migration error")

    def run(self):
        self.cur.execute(SQL_STATEMENT)
        self.con.commit()
        self.system_crit(
            "./manage.py migrate authentik_stages_authenticator_static 0008_initial --fake"
        )
        self.system_crit(
            "./manage.py migrate authentik_stages_authenticator_static 0009_throttling --fake"
        )
        self.system_crit(
            "./manage.py migrate authentik_stages_authenticator_totp 0008_initial --fake"
        )
        self.system_crit(
            "./manage.py migrate authentik_stages_authenticator_totp 0009_auto_20190420_0723 --fake"
        )
