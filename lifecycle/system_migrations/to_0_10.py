# flake8: noqa
from lifecycle.migrate import BaseMigration

SQL_STATEMENT = """
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
"""


class Migration(BaseMigration):
    def needs_migration(self) -> bool:
        self.cur.execute(
            "select * from information_schema.tables WHERE table_name='oidc_provider_client'"
        )
        return bool(self.cur.rowcount)

    def run(self):
        with self.con.transaction():
            self.cur.execute(SQL_STATEMENT)
            self.system_crit("./manage.py migrate passbook_stages_prompt")
            self.fake_migration(
                ("passbook_flows", "0008_default_flows"),
                ("passbook_flows", "0009_source_flows"),
                ("passbook_flows", "0010_provider_flows"),
            )
            self.system_crit("./manage.py migrate passbook_flows")
            self.fake_migration(("passbook_stages_password", ""))
