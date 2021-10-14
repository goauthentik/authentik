"""Test Static API"""
from django.urls import reverse
from django_otp.plugins.otp_static.models import StaticDevice
from rest_framework.test import APITestCase

from authentik.core.models import User


class AuthenticatorStaticStageTests(APITestCase):
    """Test Static API"""

    def test_api_delete(self):
        """Test api delete"""
        user = User.objects.create(username="foo")
        self.client.force_login(user)
        dev = StaticDevice.objects.create(user=user)
        response = self.client.delete(
            reverse("authentik_api:staticdevice-detail", kwargs={"pk": dev.pk})
        )
        self.assertEqual(response.status_code, 204)
