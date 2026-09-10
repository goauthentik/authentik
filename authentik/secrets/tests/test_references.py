"""Secret references enforce permissions at the API boundary."""

from django.apps import apps
from django.test import TestCase
from django.urls import reverse
from rest_framework.exceptions import PermissionDenied
from rest_framework.test import APIRequestFactory, APITestCase

from authentik.core.tests.utils import create_test_user
from authentik.providers.oauth2.models import OAuth2Provider
from authentik.secrets.models import Secret


class TestSecretReferenceFields(TestCase):
    """Every consumer serializer must enforce the same reference permission."""

    def test_consumer_fields(self):
        user = create_test_user()
        secret = Secret.objects.create(name="restricted", value="{}")
        other = Secret.objects.create(name="other", value="{}")
        request = APIRequestFactory().patch("/")
        request.user = user
        user.assign_perms_to_managed_role("authentik_secrets.view_secret", secret)
        for model in apps.get_models():
            for relation in model._meta.fields:
                if relation.related_model is not Secret:
                    continue
                instance = model(**{relation.name: secret})
                serializer = instance.serializer(context={"request": request})
                if relation.name not in serializer.fields:
                    continue
                with self.subTest(model=model._meta.label, field=relation.name):
                    field = serializer.fields[relation.name]
                    with self.assertRaises(PermissionDenied):
                        field.run_validation(str(secret.pk))
                    serializer.instance = instance
                    self.assertEqual(field.run_validation(str(secret.pk)), secret)
                    with self.assertRaises(PermissionDenied):
                        field.run_validation(str(other.pk))
                    user.assign_perms_to_managed_role("authentik_secrets.view_secret_value", other)
                    self.assertEqual(field.run_validation(str(other.pk)), other)
                    user.remove_perms_from_managed_role(
                        "authentik_secrets.view_secret_value", other
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
        user.assign_perms_to_managed_role("authentik_secrets.view_secret_value", secret)
        response = self.client.patch(url, {"secret": str(secret.pk)})
        self.assertEqual(response.status_code, 200, response.content)
        provider.refresh_from_db()
        self.assertEqual(provider.secret, secret)
