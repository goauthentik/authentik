"""Test WebAuthn API"""
from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.models import User
from authentik.stages.authenticator_webauthn.models import WebAuthnDevice


class AuthenticatorWebAuthnStage(APITestCase):
    """Test WebAuthn API"""

    def test_api_delete(self):
        """Test api delete"""
        user = User.objects.create(username="foo")
        self.client.force_login(user)
        dev = WebAuthnDevice.objects.create(user=user)
        response = self.client.delete(
            reverse("authentik_api:webauthndevice-detail", kwargs={"pk": dev.pk})
        )
        self.assertEqual(response.status_code, 204)
