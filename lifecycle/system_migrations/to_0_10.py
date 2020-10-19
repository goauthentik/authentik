from os import system

from lifecycle.migrate import BaseMigration

SQL_STATEMENT = """delete from django_migrations where app = 'passbook_stages_prompt';
drop table passbook_stages_prompt_prompt cascade;
drop table passbook_stages_prompt_promptstage cascade;
drop table passbook_stages_prompt_promptstage_fields;
drop table corsheaders_corsmodel cascade;
drop table oauth2_provider_accesstoken cascade;
drop table oauth2_provider_grant cascade;
drop table oauth2_provider_refreshtoken cascade;
drop table oidc_provider_client cascade;
drop table oidc_provider_client_response_types cascade;
drop table oidc_provider_code cascade;
drop table oidc_provider_responsetype cascade;
drop table oidc_provider_rsakey cascade;
drop table oidc_provider_token cascade;
drop table oidc_provider_userconsent cascade;
drop table passbook_providers_app_gw_applicationgatewayprovider cascade;
delete from django_migrations where app = 'passbook_flows' and name = '0008_default_flows';
delete from django_migrations where app = 'passbook_flows' and name = '0009_source_flows';
delete from django_migrations where app = 'passbook_flows' and name = '0010_provider_flows';
delete from django_migrations where app = 'passbook_stages_password' and
name = '0002_passwordstage_change_flow';"""


class Migration(BaseMigration):

    def needs_migration(self) -> bool:
        self.cur.execute(
            "select * from information_schema.tables where table_name='oidc_provider_client'"
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
        self.system_crit(
            "./manage.py migrate passbook_flows 0010_provider_flows --fake"
        )
        self.system_crit("./manage.py migrate passbook_flows")
        self.system_crit("./manage.py migrate passbook_stages_password --fake")
