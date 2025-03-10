"""Test Devices API"""

from json import loads

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.tests.utils import create_test_admin_user, create_test_user


class TestDevicesAPI(APITestCase):
    """Test applications API"""

    def setUp(self) -> None:
        self.admin = create_test_admin_user()
        self.user1 = create_test_user()
        self.device1 = self.user1.staticdevice_set.create()
        self.user2 = create_test_user()
        self.device2 = self.user2.staticdevice_set.create()

    def test_user_api(self):
        """Test user API"""
        self.client.force_login(self.user1)
        response = self.client.get(
            reverse(
                "authentik_api:device-list",
            )
        )
        self.assertEqual(response.status_code, 200)
        body = loads(response.content.decode())
        self.assertEqual(len(body), 1)
        self.assertEqual(body[0]["pk"], str(self.device1.pk))

    def test_user_api_as_admin(self):
        """Test user API"""
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse(
                "authentik_api:device-list",
            )
        )
        self.assertEqual(response.status_code, 200)
        body = loads(response.content.decode())
        self.assertEqual(len(body), 0)

    def test_admin_api(self):
        """Test admin API"""
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse(
                "authentik_api:admin-device-list",
            )
        )
        self.assertEqual(response.status_code, 200)
        body = loads(response.content.decode())
        self.assertEqual(len(body), 2)
        self.assertEqual(
            {body[0]["pk"], body[1]["pk"]}, {str(self.device1.pk), str(self.device2.pk)}
        )
