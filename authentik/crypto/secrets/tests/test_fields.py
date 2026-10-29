"""Consumer references accept only compatible secret types."""

from base64 import b64encode

from django.test import TestCase
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.serializers import Serializer

from authentik.blueprints.v1.importer import SERIALIZER_CONTEXT_CREATED, SERIALIZER_CONTEXT_USER
from authentik.core.tests.utils import create_test_user
from authentik.crypto.secrets.api import SecretReferenceField
from authentik.crypto.secrets.models import Secret, SecretType


class TestSecretReferenceTypes(TestCase):
    def test_reference_types(self):
        for field, allowed in [
            (SecretReferenceField(queryset=Secret.objects.all()), {SecretType.TEXT}),
            (
                SecretReferenceField(
                    queryset=Secret.objects.all(), allowed_types=(SecretType.JSON,)
                ),
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


class TestSecretReferenceBlueprintUser(TestCase):
    """Blueprints imported by a user check that user's permissions after tags resolve."""

    def run_field(self, secret: Secret, **context):
        field = SecretReferenceField(queryset=Secret.objects.all())
        field.bind("secret", Serializer(context=context))
        return field.run_validation(str(secret.pk))

    def test_blueprint_user(self):
        user = create_test_user()
        secret = Secret.objects.create(name="restricted")
        with self.assertRaises(PermissionDenied):
            self.run_field(secret, **{SERIALIZER_CONTEXT_USER: user})
        # A secret created earlier in the same import
        self.assertEqual(
            self.run_field(
                secret,
                **{
                    SERIALIZER_CONTEXT_USER: user,
                    SERIALIZER_CONTEXT_CREATED: {(Secret, secret.pk)},
                },
            ),
            secret,
        )
        # Blueprints applied by authentik itself
        self.assertEqual(self.run_field(secret), secret)
        user.assign_perms_to_managed_role("authentik_crypto_secrets.view_secret_value", secret)
        self.assertEqual(self.run_field(secret, **{SERIALIZER_CONTEXT_USER: user}), secret)
