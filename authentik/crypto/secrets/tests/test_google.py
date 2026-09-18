"""Google credential references remain structured when their values change."""

from base64 import b64encode
from itertools import product

from django.core.exceptions import ValidationError
from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.tests.utils import create_test_admin_user
from authentik.crypto.secrets.models import Secret, SecretType
from authentik.crypto.secrets.tests.utils import create_test_secret
from authentik.enterprise.endpoints.connectors.google_chrome.models import GoogleChromeConnector
from authentik.enterprise.providers.google_workspace.models import GoogleWorkspaceProvider
from authentik.enterprise.stages.authenticator_endpoint_gdtc.models import (
    AuthenticatorEndpointGDTCStage,
)
from authentik.events.models import Event, EventAction

GOOGLE_CONSUMERS = (GoogleWorkspaceProvider, GoogleChromeConnector, AuthenticatorEndpointGDTCStage)


class TestGoogleSecretReplacement(APITestCase):
    def setUp(self):
        self.client.force_login(create_test_admin_user())

    def test_replacement_preserves_structure(self):
        for model, secret_type in product(
            GOOGLE_CONSUMERS, (SecretType.MULTILINE, SecretType.FILE)
        ):
            with self.subTest(model=model.__name__, type=secret_type):
                value = "e30=" if secret_type == SecretType.FILE else "{}"
                secret = create_test_secret(value, secret_type)
                model.objects.create(name=secret.name, secret=secret)
                for replacement in ("[]", "invalid: [", '{"token":"updated"}'):
                    encoded = (
                        b64encode(replacement.encode()).decode()
                        if secret_type == SecretType.FILE
                        else replacement
                    )
                    response = self.client.patch(
                        reverse("authentik_api:secret-detail", kwargs={"pk": secret.pk}),
                        {"value": encoded},
                    )
                    if replacement.startswith("{"):
                        self.assertEqual(response.status_code, 200, response.content)
                        secret.refresh_from_db()
                        self.assertEqual(secret.get_json(), {"token": "updated"})
                    else:
                        self.assertEqual(response.status_code, 400, response.content)
                        with self.assertRaises(ValidationError):
                            secret.replace_value(encoded)
                        secret.refresh_from_db()
                        self.assertEqual(secret.value, value)

    def test_legacy_text_credential_cannot_be_rotated(self):
        for model in GOOGLE_CONSUMERS:
            with self.subTest(model=model.__name__):
                secret = Secret.objects.create(name=model.__name__, value="{}")
                model.objects.create(name=secret.name, secret=secret)
                response = self.client.post(
                    reverse("authentik_api:secret-rotate", kwargs={"pk": secret.pk})
                )
                self.assertEqual(response.status_code, 400, response.content)
                with self.assertRaises(ValidationError):
                    secret.rotate()
                secret.refresh_from_db()
                self.assertEqual(secret.value, "{}")
        self.assertFalse(Event.objects.filter(action=EventAction.SECRET_ROTATE).exists())
