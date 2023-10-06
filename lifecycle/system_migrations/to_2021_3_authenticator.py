# flake8: noqa
from lifecycle.migrate import BaseMigration

SQL_STATEMENT = """
ALTER TABLE authentik_stages_otp_static_otpstaticstage RENAME TO authentik_stages_authenticator_static_otpstaticstage;
UPDATE django_migrations SET app = replace(app, 'authentik_stages_otp_static', 'authentik_stages_authenticator_static');
UPDATE django_content_type SET app_label = replace(app_label, 'authentik_stages_otp_static', 'authentik_stages_authenticator_static');

ALTER TABLE authentik_stages_otp_time_otptimestage RENAME TO authentik_stages_authenticator_totp_otptimestage;
UPDATE django_migrations SET app = replace(app, 'authentik_stages_otp_time', 'authentik_stages_authenticator_totp');
UPDATE django_content_type SET app_label = replace(app_label, 'authentik_stages_otp_time', 'authentik_stages_authenticator_totp');

ALTER TABLE authentik_stages_otp_validate_otpvalidatestage RENAME TO authentik_stages_authenticator_validate_otpvalidatestage;
UPDATE django_migrations SET app = replace(app, 'authentik_stages_otp_validate', 'authentik_stages_authenticator_validate');
UPDATE django_content_type SET app_label = replace(app_label, 'authentik_stages_otp_validate', 'authentik_stages_authenticator_validate');
"""


class Migration(BaseMigration):
    def needs_migration(self) -> bool:
        self.cur.execute(
            "select * from information_schema.tables where table_name ="
            " 'authentik_stages_otp_static_otpstaticstage';"
        )
        return bool(self.cur.rowcount)

    def run(self):
        with self.con.transaction():
            self.cur.execute(SQL_STATEMENT)
