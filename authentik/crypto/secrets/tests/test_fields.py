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
                {SecretType.JSON},
            ),
            (
                SecretReferenceField(
                    queryset=Secret.objects.all(),
                    allowed_types=(SecretType.TEXT, SecretType.FILE),
                ),
                {SecretType.TEXT, SecretType.FILE},
            ),
        ]:
            field.bind("secret", Serializer())
            for secret_type in SecretType:
                with self.subTest(field=type(field).__name__, type=secret_type, allowed=allowed):
                    secret = Secret.objects.create(
                        name=f"{Secret.objects.count()}",
                        type=secret_type,
                        secret_value=(
                            b64encode(b"{}").decode() if secret_type == SecretType.FILE else "{}"
                        ),
                    )
                    if secret_type in allowed:
                        self.assertEqual(field.run_validation(str(secret.pk)), secret)
                    else:
                        with self.assertRaises(ValidationError):
                            field.run_validation(str(secret.pk))
