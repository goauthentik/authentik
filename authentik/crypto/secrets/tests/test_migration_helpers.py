"""Credential backfills preserve references when run again."""

from django.apps import apps
from django.db import connection
from django.test import TestCase

from authentik.crypto.secrets.migrations._credential_values import migrate_credentials
from authentik.crypto.secrets.models import Secret, SecretType
from authentik.providers.oauth2.models import OAuth2Provider


class TestCredentialBackfill(TestCase):
    def test_existing_reference_is_not_replaced(self):
        provider = OAuth2Provider.objects.create(name="existing", _client_secret="legacy")
        original = provider.secret
        original.replace_value("current")
        count = Secret.objects.count()
        with connection.schema_editor(atomic=False) as editor:
            migrate_credentials(
                apps,
                editor,
                "authentik_providers_oauth2",
                "OAuth2Provider",
                [("_client_secret", "secret", "text", "client secret")],
                include_empty=True,
            )
        provider.refresh_from_db()
        self.assertEqual(provider.secret_id, original.pk)
        self.assertEqual(provider.secret.value, "current")
        self.assertEqual(Secret.objects.count(), count)

    def test_scalar_type_does_not_depend_on_newlines(self):
        provider = OAuth2Provider.objects.create(name="scalar", _client_secret="legacy\nvalue")
        OAuth2Provider.objects.filter(pk=provider.pk).update(secret=None)
        with connection.schema_editor(atomic=False) as editor:
            migrate_credentials(
                apps,
                editor,
                "authentik_providers_oauth2",
                "OAuth2Provider",
                [("_client_secret", "secret", None, "client secret")],
            )
        provider.refresh_from_db()
        self.assertEqual(provider.secret.type, SecretType.TEXT)
        self.assertEqual(provider.secret.value, "legacy\nvalue")
