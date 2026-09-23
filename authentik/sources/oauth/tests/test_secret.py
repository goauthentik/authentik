"""OAuth sources require the credential representation their client consumes."""

from django.test import TestCase

from authentik.crypto.secrets.models import Secret, SecretType
from authentik.sources.oauth.api.source import OAuthSourceSerializer


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
                            "consumer_secret_ref": str(secret.pk),
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
                        self.assertIn("consumer_secret_ref", changed.errors)
                        source.delete()
