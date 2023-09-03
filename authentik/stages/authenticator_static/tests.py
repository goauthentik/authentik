"""Test Static API"""
from django.test.utils import override_settings
from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.models import User
from authentik.core.tests.utils import create_test_admin_user
from authentik.lib.generators import generate_id
from authentik.stages.authenticator.tests import TestCase, ThrottlingTestMixin
from authentik.stages.authenticator_static.models import StaticDevice


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


class DeviceTest(TestCase):
    """A few generic tests to get us started."""

    def setUp(self):
        try:
            self.user = create_test_admin_user("alice")
        except Exception:
            self.skipTest("Unable to create the test user.")

    def test_str(self):
        device = StaticDevice.objects.create(user=self.user, name="Device")

        str(device)

    def test_str_unpopulated(self):
        device = StaticDevice()

        str(device)


@override_settings(
    OTP_STATIC_THROTTLE_FACTOR=1,
)
class ThrottlingTestCase(ThrottlingTestMixin, TestCase):
    def setUp(self):
        user = create_test_admin_user("alice")
        self.device = user.staticdevice_set.create()
        self.device.token_set.create(token=generate_id())
        self.device.token_set.create(token=generate_id())
        self.device.token_set.create(token=generate_id())

    def valid_token(self):
        return self.device.token_set.first().token

    def invalid_token(self):
        return "bogus"
