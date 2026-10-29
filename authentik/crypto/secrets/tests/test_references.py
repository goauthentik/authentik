"""Secret references enforce permissions at the API boundary."""

from json import dumps

from django.apps import apps
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from rest_framework.exceptions import PermissionDenied
from rest_framework.test import APIRequestFactory, APITestCase

from authentik.core.tests.utils import create_test_flow, create_test_user
from authentik.crypto.secrets.models import Secret
from authentik.lib.generators import generate_id
from authentik.providers.oauth2.models import OAuth2Provider


class TestSecretReferenceFields(TestCase):
    """Every consumer serializer must enforce the same reference permission."""

    def test_consumer_fields(self):
        user = create_test_user()
        secret = Secret.objects.create(name="restricted", secret_value="{}")
        other = Secret.objects.create(name="other", secret_value="{}")
        request = APIRequestFactory().patch("/")
        request.user = user
        user.assign_perms_to_managed_role("authentik_crypto_secrets.view_secret", secret)
        for model in apps.get_models():
            for relation in model._meta.fields:
                if relation.related_model is not Secret:
                    continue
                self.assertTrue(relation.name.endswith("_ref"), f"{model.__name__}.{relation.name}")
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
                    user.assign_perms_to_managed_role(
                        "authentik_crypto_secrets.view_secret_value", other
                    )
                    self.assertEqual(field.run_validation(str(other.pk)), other)
                    user.remove_perms_from_managed_role(
                        "authentik_crypto_secrets.view_secret_value", other
                    )


class TestSecretReferenceAPI(APITestCase):
    def test_provider_edit_does_not_grant_access_to_other_secrets(self):
        user = create_test_user()
        provider = OAuth2Provider.objects.create(name="provider")
        secret = Secret.objects.create(name="restricted", secret_value="{}")
        user.assign_perms_to_managed_role(
            [
                "authentik_providers_oauth2.view_oauth2provider",
                "authentik_providers_oauth2.change_oauth2provider",
            ],
            provider,
        )
        self.client.force_login(user)
        url = reverse("authentik_api:oauth2provider-detail", kwargs={"pk": provider.pk})
        response = self.client.patch(url, {"client_secret_ref": str(secret.pk)})
        self.assertEqual(response.status_code, 403)
        provider.refresh_from_db()
        self.assertNotEqual(provider.client_secret_ref, secret)
        response = self.client.patch(
            url, {"name": "renamed", "client_secret_ref": str(provider.client_secret_ref_id)}
        )
        self.assertEqual(response.status_code, 200, response.content)
        user.assign_perms_to_managed_role("authentik_crypto_secrets.view_secret_value", secret)
        response = self.client.patch(url, {"client_secret_ref": str(secret.pk)})
        self.assertEqual(response.status_code, 200, response.content)
        provider.refresh_from_db()
        self.assertEqual(provider.client_secret_ref, secret)


class TestSecretReferenceBlueprint(APITestCase):
    """Blueprint imports check references once tags are resolved."""

    def setUp(self) -> None:
        self.user = create_test_user()
        self.user.assign_perms_to_managed_role(
            [
                "authentik_blueprints.add_blueprintinstance",
                *[
                    f"{app}.{action}_{model}"
                    for app, model in [
                        ("authentik_providers_oauth2", "oauth2provider"),
                        ("authentik_crypto_secrets", "secret"),
                    ]
                    for action in ["add", "change", "delete"]
                ],
            ]
        )
        self.client.force_login(self.user)
        self.secret = Secret.objects.create(name="restricted")
        self.flow = create_test_flow()

    def import_provider(self, name: str, identifiers: str = "", attrs: str = "", context=None):
        blueprint = f"""
version: 1
entries:
  - model: authentik_crypto_secrets.secret
    id: created
    identifiers:
      name: {name} created
  - model: authentik_providers_oauth2.oauth2provider
    identifiers:
      name: {name}
      {identifiers}
    attrs:
      authorization_flow: {self.flow.pk}
      invalidation_flow: {self.flow.pk}
      redirect_uris: []
      {attrs}
"""
        data = {"file": SimpleUploadedFile("blueprint.yaml", blueprint.encode())}
        if context:
            data["context"] = dumps(context)
        return self.client.post(
            reverse("authentik_api:blueprintinstance-import"), data, format="multipart"
        )

    def test_references_need_value_permission(self):
        for label, kwargs in [
            ("uuid", {"attrs": f"client_secret_ref: {self.secret.pk}"}),
            (
                "find",
                {
                    "attrs": (
                        "client_secret_ref: "
                        "!Find [authentik_crypto_secrets.secret, [name, restricted]]"
                    )
                },
            ),
            (
                "context",
                {
                    "attrs": "client_secret_ref: !Context secret",
                    "context": {"secret": str(self.secret.pk)},
                },
            ),
            ("identifiers", {"identifiers": f"client_secret_ref: {self.secret.pk}"}),
        ]:
            with self.subTest(label):
                name = generate_id()
                response = self.import_provider(name, **kwargs)
                self.assertEqual(
                    response.json(), {"detail": "You do not have permission to use this secret."}
                )
                self.assertFalse(OAuth2Provider.objects.filter(name=name).exists())

        self.user.assign_perms_to_managed_role(
            "authentik_crypto_secrets.view_secret_value", self.secret
        )
        name = generate_id()
        response = self.import_provider(
            name,
            attrs="client_secret_ref: !Find [authentik_crypto_secrets.secret, [name, restricted]]",
        )
        self.assertTrue(response.json()["imported"], response.content)
        self.assertEqual(OAuth2Provider.objects.get(name=name).client_secret_ref, self.secret)

    def test_reference_created_secret(self):
        name = generate_id()
        response = self.import_provider(name, attrs="client_secret_ref: !KeyOf created")
        self.assertTrue(response.json()["imported"], response.content)
        self.assertEqual(
            OAuth2Provider.objects.get(name=name).client_secret_ref,
            Secret.objects.get(name=f"{name} created"),
        )
