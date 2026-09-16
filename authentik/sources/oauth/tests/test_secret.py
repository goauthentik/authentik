"""OAuth sources require the credential representation their client consumes."""

from importlib import import_module

from django.apps import apps
from django.db import connection
from django.test import TestCase

from authentik.crypto.secrets.models import Secret, SecretType
from authentik.sources.oauth.api.source import OAuthSourceSerializer
from authentik.sources.oauth.models import OAuthSource


class TestSourceSecretTypes(TestCase):
    def test_source_types_and_provider_changes(self):
        for provider_type, expected in [
            ("apple", SecretType.MULTILINE),
            ("github", SecretType.TEXT),
        ]:
            for secret_type in SecretType:
                with self.subTest(provider=provider_type, type=secret_type):
                    secret = Secret.objects.create(
                        name=f"{provider_type}-{secret_type}", type=secret_type, value="credential"
                    )
                    serializer = OAuthSourceSerializer(
                        data={
                            "name": "source",
                            "slug": "source",
                            "enabled": False,
                            "provider_type": provider_type,
                            "consumer_key": "client",
                            "secret": str(secret.pk),
                        }
                    )
                    self.assertEqual(
                        serializer.is_valid(), secret_type == expected, serializer.errors
                    )
                    if secret_type == expected:
                        source = serializer.save()
                        changed = OAuthSourceSerializer(
                            instance=source,
                            data={
                                "provider_type": "github" if provider_type == "apple" else "apple",
                            },
                            partial=True,
                        )
                        self.assertFalse(changed.is_valid())
                        self.assertIn("secret", changed.errors)
                        source.delete()

    def test_migration_uses_provider_type(self):
        migration = import_module("authentik.sources.oauth.migrations.0016_oauthsource_secret")
        for provider_type in ["apple", "github"]:
            OAuthSource.objects.create(
                name=provider_type,
                slug=provider_type,
                provider_type=provider_type,
                _consumer_secret="credential\nvalue",
            )
        with connection.schema_editor(atomic=False) as editor:
            migration.migrate_consumer_secret(apps, editor)
        for provider_type, expected in [
            ("apple", SecretType.MULTILINE),
            ("github", SecretType.TEXT),
        ]:
            source = OAuthSource.objects.get(slug=provider_type)
            self.assertEqual(source.secret.type, expected)
            self.assertEqual(source.secret.value, "credential\nvalue")
