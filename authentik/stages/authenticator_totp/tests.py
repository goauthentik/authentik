"""Test TOTP API"""
from django.urls import reverse
from django_otp.plugins.otp_totp.models import TOTPDevice
from rest_framework.test import APITestCase

from authentik.core.models import User


class AuthenticatorTOTPStage(APITestCase):
    """Test TOTP API"""

    def test_api_delete(self):
        """Test api delete"""
        user = User.objects.create(username="foo")
        self.client.force_login(user)
        dev = TOTPDevice.objects.create(user=user)
        response = self.client.delete(
            reverse("authentik_api:totpdevice-detail", kwargs={"pk": dev.pk})
        )
        self.assertEqual(response.status_code, 204)
