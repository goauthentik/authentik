# flake8: noqa
from redis import Redis

from authentik.lib.config import CONFIG
from lifecycle.migrate import BaseMigration

SQL_STATEMENT = """BEGIN TRANSACTION;
ALTER TABLE passbook_audit_event RENAME TO authentik_audit_event;
ALTER TABLE passbook_core_application RENAME TO authentik_core_application;
ALTER TABLE passbook_core_group RENAME TO authentik_core_group;
ALTER TABLE passbook_core_propertymapping RENAME TO authentik_core_propertymapping;
ALTER TABLE passbook_core_provider RENAME TO authentik_core_provider;
ALTER TABLE passbook_core_provider_property_mappings RENAME TO authentik_core_provider_property_mappings;
ALTER TABLE passbook_core_source RENAME TO authentik_core_source;
ALTER TABLE passbook_core_source_property_mappings RENAME TO authentik_core_source_property_mappings;
ALTER TABLE passbook_core_token RENAME TO authentik_core_token;
ALTER TABLE passbook_core_user RENAME TO authentik_core_user;
ALTER TABLE passbook_core_user_groups RENAME TO authentik_core_user_groups;
ALTER TABLE passbook_core_user_pb_groups RENAME TO authentik_core_user_pb_groups;
ALTER TABLE passbook_core_user_user_permissions RENAME TO authentik_core_user_user_permissions;
ALTER TABLE passbook_core_usersourceconnection RENAME TO authentik_core_usersourceconnection;
ALTER TABLE passbook_crypto_certificatekeypair RENAME TO authentik_crypto_certificatekeypair;
ALTER TABLE passbook_flows_flow RENAME TO authentik_flows_flow;
ALTER TABLE passbook_flows_flowstagebinding RENAME TO authentik_flows_flowstagebinding;
ALTER TABLE passbook_flows_stage RENAME TO authentik_flows_stage;
ALTER TABLE passbook_outposts_outpost RENAME TO authentik_outposts_outpost;
ALTER TABLE passbook_outposts_outpost_providers RENAME TO authentik_outposts_outpost_providers;
ALTER TABLE passbook_outposts_dockerserviceconnection RENAME TO authentik_outposts_dockerserviceconnection;
ALTER TABLE passbook_outposts_kubernetesserviceconnection RENAME TO authentik_outposts_kubernetesserviceconnection;
ALTER TABLE passbook_outposts_outpostserviceconnection RENAME TO authentik_outposts_outpostserviceconnection;
ALTER TABLE passbook_policies_dummy_dummypolicy RENAME TO authentik_policies_dummy_dummypolicy;
ALTER TABLE passbook_policies_expiry_passwordexpirypolicy RENAME TO authentik_policies_expiry_passwordexpirypolicy;
ALTER TABLE passbook_policies_expression_expressionpolicy RENAME TO authentik_policies_expression_expressionpolicy;
ALTER TABLE passbook_policies_group_membership_groupmembershippolicy RENAME TO authentik_policies_group_membership_groupmembershippolicy;
ALTER TABLE passbook_policies_hibp_haveibeenpwendpolicy RENAME TO authentik_policies_hibp_haveibeenpwendpolicy;
ALTER TABLE passbook_policies_password_passwordpolicy RENAME TO authentik_policies_password_passwordpolicy;
ALTER TABLE passbook_policies_policy RENAME TO authentik_policies_policy;
ALTER TABLE passbook_policies_policybinding RENAME TO authentik_policies_policybinding;
ALTER TABLE passbook_policies_policybindingmodel RENAME TO authentik_policies_policybindingmodel;
ALTER TABLE passbook_policies_reputation_ipreputation RENAME TO authentik_policies_reputation_ipreputation;
ALTER TABLE passbook_policies_reputation_reputationpolicy RENAME TO authentik_policies_reputation_reputationpolicy;
ALTER TABLE passbook_policies_reputation_userreputation RENAME TO authentik_policies_reputation_userreputation;
ALTER TABLE passbook_providers_oauth2_authorizationcode RENAME TO authentik_providers_oauth2_authorizationcode;
ALTER TABLE passbook_providers_oauth2_oauth2provider RENAME TO authentik_providers_oauth2_oauth2provider;
ALTER TABLE passbook_providers_oauth2_refreshtoken RENAME TO authentik_providers_oauth2_refreshtoken;
ALTER TABLE passbook_providers_oauth2_scopemapping RENAME TO authentik_providers_oauth2_scopemapping;
ALTER TABLE passbook_providers_proxy_proxyprovider RENAME TO authentik_providers_proxy_proxyprovider;
ALTER TABLE passbook_providers_saml_samlpropertymapping RENAME TO authentik_providers_saml_samlpropertymapping;
ALTER TABLE passbook_providers_saml_samlprovider RENAME TO authentik_providers_saml_samlprovider;
ALTER TABLE passbook_sources_ldap_ldappropertymapping RENAME TO authentik_sources_ldap_ldappropertymapping;
ALTER TABLE passbook_sources_ldap_ldapsource RENAME TO authentik_sources_ldap_ldapsource;
ALTER TABLE passbook_sources_oauth_oauthsource RENAME TO authentik_sources_oauth_oauthsource;
ALTER TABLE passbook_sources_oauth_useroauthsourceconnection RENAME TO authentik_sources_oauth_useroauthsourceconnection;
ALTER TABLE passbook_sources_saml_samlsource RENAME TO authentik_sources_saml_samlsource;
ALTER TABLE passbook_stages_captcha_captchastage RENAME TO authentik_stages_captcha_captchastage;
ALTER TABLE passbook_stages_consent_consentstage RENAME TO authentik_stages_consent_consentstage;
ALTER TABLE passbook_stages_consent_userconsent RENAME TO authentik_stages_consent_userconsent;
ALTER TABLE passbook_stages_dummy_dummystage RENAME TO authentik_stages_dummy_dummystage;
ALTER TABLE passbook_stages_email_emailstage RENAME TO authentik_stages_email_emailstage;
ALTER TABLE passbook_stages_identification_identificationstage RENAME TO authentik_stages_identification_identificationstage;
ALTER TABLE passbook_stages_invitation_invitation RENAME TO authentik_stages_invitation_invitation;
ALTER TABLE passbook_stages_invitation_invitationstage RENAME TO authentik_stages_invitation_invitationstage;
ALTER TABLE passbook_stages_otp_static_otpstaticstage RENAME TO authentik_stages_otp_static_otpstaticstage;
ALTER TABLE passbook_stages_otp_time_otptimestage RENAME TO authentik_stages_otp_time_otptimestage;
ALTER TABLE passbook_stages_otp_validate_otpvalidatestage RENAME TO authentik_stages_otp_validate_otpvalidatestage;
ALTER TABLE passbook_stages_password_passwordstage RENAME TO authentik_stages_password_passwordstage;
ALTER TABLE passbook_stages_prompt_prompt RENAME TO authentik_stages_prompt_prompt;
ALTER TABLE passbook_stages_prompt_promptstage RENAME TO authentik_stages_prompt_promptstage;
ALTER TABLE passbook_stages_prompt_promptstage_fields RENAME TO authentik_stages_prompt_promptstage_fields;
ALTER TABLE passbook_stages_prompt_promptstage_validation_policies RENAME TO authentik_stages_prompt_promptstage_validation_policies;
ALTER TABLE passbook_stages_user_delete_userdeletestage RENAME TO authentik_stages_user_delete_userdeletestage;
ALTER TABLE passbook_stages_user_login_userloginstage RENAME TO authentik_stages_user_login_userloginstage;
ALTER TABLE passbook_stages_user_logout_userlogoutstage RENAME TO authentik_stages_user_logout_userlogoutstage;
ALTER TABLE passbook_stages_user_write_userwritestage RENAME TO authentik_stages_user_write_userwritestage;

ALTER SEQUENCE passbook_core_provider_id_seq RENAME TO authentik_core_provider_id_seq;
ALTER SEQUENCE passbook_core_provider_property_mappings_id_seq RENAME TO authentik_core_provider_property_mappings_id_seq;
ALTER SEQUENCE passbook_core_source_property_mappings_id_seq RENAME TO authentik_core_source_property_mappings_id_seq;
ALTER SEQUENCE passbook_core_user_groups_id_seq RENAME TO authentik_core_user_groups_id_seq;
ALTER SEQUENCE passbook_core_user_id_seq RENAME TO authentik_core_user_id_seq;
ALTER SEQUENCE passbook_core_user_pb_groups_id_seq RENAME TO authentik_core_user_pb_groups_id_seq;
ALTER SEQUENCE passbook_core_user_user_permissions_id_seq RENAME TO authentik_core_user_user_permissions_id_seq;
ALTER SEQUENCE passbook_core_usersourceconnection_id_seq RENAME TO authentik_core_usersourceconnection_id_seq;
ALTER SEQUENCE passbook_outposts_outpost_providers_id_seq RENAME TO authentik_outposts_outpost_providers_id_seq;
ALTER SEQUENCE passbook_policies_reputation_ipreputation_id_seq RENAME TO authentik_policies_reputation_ipreputation_id_seq;
ALTER SEQUENCE passbook_policies_reputation_userreputation_id_seq RENAME TO authentik_policies_reputation_userreputation_id_seq;
ALTER SEQUENCE passbook_providers_oauth2_authorizationcode_id_seq RENAME TO authentik_providers_oauth2_authorizationcode_id_seq;
ALTER SEQUENCE passbook_providers_oauth2_refreshtoken_id_seq RENAME TO authentik_providers_oauth2_refreshtoken_id_seq;
ALTER SEQUENCE passbook_stages_consent_userconsent_id_seq RENAME TO authentik_stages_consent_userconsent_id_seq;
ALTER SEQUENCE passbook_stages_prompt_promptstage_fields_id_seq RENAME TO authentik_stages_prompt_promptstage_fields_id_seq;
ALTER SEQUENCE passbook_stages_prompt_promptstage_validation_policies_id_seq RENAME TO authentik_stages_prompt_promptstage_validation_policies_id_seq;

UPDATE django_migrations SET app = replace(app, 'passbook', 'authentik');
UPDATE django_content_type SET app_label = replace(app_label, 'passbook', 'authentik');
COMMIT;
"""


class Migration(BaseMigration):
    def needs_migration(self) -> bool:
        self.cur.execute(
            "select * from information_schema.tables where table_name = 'passbook_core_user';"
        )
        return bool(self.cur.rowcount)

    def run(self):
        with self.con.transaction():
            self.cur.execute(SQL_STATEMENT)
            # We also need to clean the cache to make sure no pickeled objects still exist
            for db in [
                CONFIG.get("redis.message_queue_db"),
                CONFIG.get("redis.cache_db"),
                CONFIG.get("redis.ws_db"),
            ]:
                redis = Redis(
                    host=CONFIG.get("redis.host"),
                    port=6379,
                    db=db,
                    password=CONFIG.get("redis.password"),
                )
                redis.flushall()
