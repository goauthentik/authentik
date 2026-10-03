"""Consumer references accept only compatible secret types."""

from base64 import b64encode

from django.test import TestCase
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import Serializer

from authentik.crypto.secrets.api import JSONSecretReferenceField, SecretReferenceField
from authentik.crypto.secrets.models import Secret, SecretType


class TestSecretReferenceTypes(TestCase):
    def test_reference_types(self):
        for field, allowed in [
            (SecretReferenceField(queryset=Secret.objects.all()), {SecretType.TEXT}),
            (
                JSONSecretReferenceField(queryset=Secret.objects.all()),
                {SecretType.MULTILINE, SecretType.FILE},
            ),
            (
                SecretReferenceField(
                    queryset=Secret.objects.all(),
                    allowed_types=(SecretType.MULTILINE, SecretType.FILE),
                ),
                {SecretType.MULTILINE, SecretType.FILE},
            ),
        ]:
            field.bind("secret", Serializer())
            for secret_type in SecretType:
                with self.subTest(field=type(field).__name__, type=secret_type, allowed=allowed):
                    secret = Secret.objects.create(
                        name=f"{Secret.objects.count()}",
                        type=secret_type,
                        value=b64encode(b"{}").decode() if secret_type == SecretType.FILE else "{}",
                    )
                    if secret_type in allowed:
                        self.assertEqual(field.run_validation(str(secret.pk)), secret)
                    else:
                        with self.assertRaises(ValidationError):
                            field.run_validation(str(secret.pk))

    def test_structured_reference_rejects_scalar_content(self):
        field = JSONSecretReferenceField(queryset=Secret.objects.all())
        field.bind("secret", Serializer())
        secret = Secret.objects.create(name="scalar", type=SecretType.MULTILINE, value="plain")
        with self.assertRaises(ValidationError):
            field.run_validation(str(secret.pk))
