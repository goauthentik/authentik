"""Test Static API"""

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
        self.user = create_test_admin_user("alice")

    def test_str(self):
        """Test __str__ of model"""
        device = StaticDevice.objects.create(user=self.user, name="Device")

        str(device)

    def test_str_unpopulated(self):
        """Test __str__ of model"""
        device = StaticDevice()

        str(device)

    def test_verify_token_separators(self):
        """Test tokens entered with the displayed hyphens, or with spaces, are accepted"""
        device = StaticDevice.objects.create(user=self.user, name="Device")
        device.token_set.create(token="abcdEFGH1234")
        device.token_set.create(token="wxyzWXYZ5678")

        self.assertTrue(device.verify_token("abcd-EFGH-1234"))
        self.assertTrue(device.verify_token(" wxyz WXYZ 5678 "))
        self.assertFalse(device.token_set.exists())

    def test_verify_token_separators_wrong_token(self):
        """Test separators don't make an incorrect token valid"""
        device = StaticDevice.objects.create(user=self.user, name="Device")
        device.token_set.create(token="abcdEFGH1234")

        self.assertFalse(device.verify_token("abcd-efgh-1234"))
        self.assertFalse(device.verify_token("-"))
        self.assertTrue(device.token_set.exists())


class ThrottlingTestCase(ThrottlingTestMixin, TestCase):
    """Test static device throttling"""

    def setUp(self):
        user = create_test_admin_user("alice")
        self.device = user.staticdevice_set.create()
        self.device.token_set.create(token=generate_id(length=16))
        self.device.token_set.create(token=generate_id(length=16))
        self.device.token_set.create(token=generate_id(length=16))

    def valid_token(self):
        return self.device.token_set.first().token

    def invalid_token(self):
        return "bogus"
