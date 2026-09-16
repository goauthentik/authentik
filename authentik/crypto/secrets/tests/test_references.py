"""Secret references enforce permissions at the API boundary."""

from django.apps import apps
from django.test import TestCase
from django.urls import reverse
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.test import APIRequestFactory, APITestCase

from authentik.core.tests.utils import create_test_user
from authentik.crypto.secrets.models import Secret, SecretType
from authentik.providers.oauth2.models import OAuth2Provider


class TestSecretReferenceFields(TestCase):
    """Every consumer serializer must enforce the same reference permission."""

    def test_consumer_fields(self):
        user = create_test_user()
        secrets = {
            secret_type: [
                Secret.objects.create(
                    name=f"{name}-{secret_type}",
                    type=secret_type,
                    value="e30=" if secret_type == SecretType.FILE else "{}",
                )
                for name in ("restricted", "other")
            ]
            for secret_type in SecretType
        }
        request = APIRequestFactory().patch("/")
        request.user = user
        for model in apps.get_models():
            for relation in model._meta.fields:
                if relation.related_model is not Secret:
                    continue
                instance = model()
                serializer = instance.serializer(context={"request": request})
                if relation.name not in serializer.fields:
                    continue
                with self.subTest(model=model._meta.label, field=relation.name):
                    field = serializer.fields[relation.name]
                    secret, other = secrets[field.allowed_types[0]]
                    setattr(instance, relation.name, secret)
                    user.assign_perms_to_managed_role(
                        "authentik_crypto_secrets.view_secret", secret
                    )
                    with self.assertRaises(PermissionDenied):
                        field.run_validation(str(secret.pk))
                    serializer.instance = instance
                    self.assertEqual(field.run_validation(str(secret.pk)), secret)
                    with self.assertRaises(PermissionDenied):
                        field.run_validation(str(other.pk))
                    user.assign_perms_to_managed_role(
                        "authentik_crypto_secrets.view_secret_value", other
                    )
                    self.assertEqual(field.run_validation(str(other.pk)), other)
                    user.remove_perms_from_managed_role(
                        "authentik_crypto_secrets.view_secret_value", other
                    )
                    for secret_type in set(SecretType) - set(field.allowed_types):
                        wrong_type = secrets[secret_type][1]
                        user.assign_perms_to_managed_role(
                            "authentik_crypto_secrets.view_secret_value", wrong_type
                        )
                        with self.assertRaises(ValidationError):
                            field.run_validation(str(wrong_type.pk))
                        user.remove_perms_from_managed_role(
                            "authentik_crypto_secrets.view_secret_value", wrong_type
                        )


class TestSecretReferenceAPI(APITestCase):
    def test_provider_edit_does_not_grant_access_to_other_secrets(self):
        user = create_test_user()
        provider = OAuth2Provider.objects.create(name="provider")
        secret = Secret.objects.create(name="restricted", value="{}")
        user.assign_perms_to_managed_role(
            [
                "authentik_providers_oauth2.view_oauth2provider",
                "authentik_providers_oauth2.change_oauth2provider",
            ],
            provider,
        )
        self.client.force_login(user)
        url = reverse("authentik_api:oauth2provider-detail", kwargs={"pk": provider.pk})
        response = self.client.patch(url, {"secret": str(secret.pk)})
        self.assertEqual(response.status_code, 403)
        provider.refresh_from_db()
        self.assertNotEqual(provider.secret, secret)
        response = self.client.patch(url, {"name": "renamed", "secret": str(provider.secret_id)})
        self.assertEqual(response.status_code, 200, response.content)
        user.assign_perms_to_managed_role("authentik_crypto_secrets.view_secret_value", secret)
        response = self.client.patch(url, {"secret": str(secret.pk)})
        self.assertEqual(response.status_code, 200, response.content)
        provider.refresh_from_db()
        self.assertEqual(provider.secret, secret)
