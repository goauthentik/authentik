"""Test SMS API"""
from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.models import User
from authentik.stages.authenticator_sms.models import SMSDevice


class AuthenticatorSMSStage(APITestCase):
    """Test SMS API"""

    def test_api_delete(self):
        """Test api delete"""
        user = User.objects.create(username="foo")
        self.client.force_login(user)
        dev = SMSDevice.objects.create(user=user)
        response = self.client.delete(
            reverse("authentik_api:smsdevice-detail", kwargs={"pk": dev.pk})
        )
        self.assertEqual(response.status_code, 204)
