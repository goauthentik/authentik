# flake8: noqa
from os import system

from lifecycle.migrate import BaseMigration

SQL_STATEMENT = """
BEGIN TRANSACTION;
DELETE FROM django_migrations WHERE app = 'passbook_stages_prompt';
DROP TABLE passbook_stages_prompt_prompt cascade;
DROP TABLE passbook_stages_prompt_promptstage cascade;
DROP TABLE passbook_stages_prompt_promptstage_fields;
DROP TABLE corsheaders_corsmodel cascade;
DROP TABLE oauth2_provider_accesstoken cascade;
DROP TABLE oauth2_provider_grant cascade;
DROP TABLE oauth2_provider_refreshtoken cascade;
DROP TABLE oidc_provider_client cascade;
DROP TABLE oidc_provider_client_response_types cascade;
DROP TABLE oidc_provider_code cascade;
DROP TABLE oidc_provider_responsetype cascade;
DROP TABLE oidc_provider_rsakey cascade;
DROP TABLE oidc_provider_token cascade;
DROP TABLE oidc_provider_userconsent cascade;
DROP TABLE passbook_providers_app_gw_applicationgatewayprovider cascade;
DELETE FROM django_migrations WHERE app = 'passbook_flows' AND name = '0008_default_flows';
DELETE FROM django_migrations WHERE app = 'passbook_flows' AND name = '0009_source_flows';
DELETE FROM django_migrations WHERE app = 'passbook_flows' AND name = '0010_provider_flows';
DELETE FROM django_migrations WHERE app = 'passbook_stages_password' AND name = '0002_passwordstage_change_flow';
COMMIT;"""


class Migration(BaseMigration):
    def needs_migration(self) -> bool:
        self.cur.execute(
            "select * from information_schema.tables WHERE table_name='oidc_provider_client'"
        )
        return bool(self.cur.rowcount)

    def system_crit(self, command):
        retval = system(command)  # nosec
        if retval != 0:
            raise Exception("Migration error")

    def run(self):
        self.cur.execute(SQL_STATEMENT)
        self.con.commit()
        self.system_crit("./manage.py migrate passbook_stages_prompt")
        self.system_crit("./manage.py migrate passbook_flows 0008_default_flows --fake")
        self.system_crit("./manage.py migrate passbook_flows 0009_source_flows --fake")
        self.system_crit("./manage.py migrate passbook_flows 0010_provider_flows --fake")
        self.system_crit("./manage.py migrate passbook_flows")
        self.system_crit("./manage.py migrate passbook_stages_password --fake")
