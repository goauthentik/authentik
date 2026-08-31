"""Contract tests for models that consume managed secrets."""

from django.apps import apps
from django.db import models
from django.test import SimpleTestCase

from authentik.secrets.models import Secret

EXPECTED_CONSUMERS = {
    ("authentik_endpoints_connectors_fleet.FleetConnector", "token", "secret"),
    (
        "authentik_providers_microsoft_entra.MicrosoftEntraProvider",
        "client_secret",
        "secret",
    ),
    ("authentik_events.NotificationTransport", "webhook_url", "secret"),
    ("authentik_providers_oauth2.OAuth2Provider", "client_secret", "secret"),
    ("authentik_providers_radius.RadiusProvider", "shared_secret", "secret"),
    ("authentik_providers_scim.SCIMProvider", "token", "secret"),
    ("authentik_sources_kerberos.KerberosSource", "sync_password", "secret"),
    ("authentik_sources_ldap.LDAPSource", "bind_password", "secret"),
    ("authentik_sources_oauth.OAuthSource", "consumer_secret", "secret"),
    ("authentik_sources_plex.PlexSource", "plex_token", "secret"),
    ("authentik_sources_telegram.TelegramSource", "bot_token", "secret"),
    ("authentik_stages_authenticator_duo.AuthenticatorDuoStage", "client_secret", "secret"),
    (
        "authentik_stages_authenticator_duo.AuthenticatorDuoStage",
        "admin_secret_key",
        "admin_secret",
    ),
    ("authentik_stages_authenticator_email.AuthenticatorEmailStage", "password", "secret"),
    ("authentik_stages_authenticator_sms.AuthenticatorSMSStage", "auth", "auth_secret"),
    (
        "authentik_stages_authenticator_sms.AuthenticatorSMSStage",
        "auth_password",
        "auth_password_secret",
    ),
    ("authentik_stages_captcha.CaptchaStage", "private_key", "secret"),
    ("authentik_stages_email.EmailStage", "password", "secret"),
}


class TestSecretConsumers(SimpleTestCase):
    """Keep migration columns and public API fields aligned across every consumer."""

    def test_consumer_contract(self):
        for label, legacy_attribute, secret_field in EXPECTED_CONSUMERS:
            model = apps.get_model(label)
            retained = model._meta.get_field(f"_{legacy_attribute}")
            self.assertEqual(retained.db_column, legacy_attribute)

            reference = model._meta.get_field(secret_field)
            self.assertIs(reference.related_model, Secret)
            self.assertIs(reference.remote_field.on_delete, models.PROTECT)

            fields = model().serializer().fields
            self.assertIn(secret_field, fields)
            self.assertNotIn(legacy_attribute, fields)
            self.assertNotIn(f"_{legacy_attribute}", fields)
            self.assertNotIn(legacy_attribute, model.__dict__)
