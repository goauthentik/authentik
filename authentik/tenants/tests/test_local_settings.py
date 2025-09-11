"""Test Settings API"""

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.tests.utils import create_test_admin_user
from authentik.tenants.flags import Flag


class TestLocalSettingsAPI(APITestCase):
    """Test settings API"""

    def setUp(self):
        super().setUp()
        self.local_admin = create_test_admin_user()

    def test_settings_flags(self):
        """Test settings API"""

        class TestFlag(Flag[bool], key="tenants_test_flag"):

            default = False
            visibility = "public"

        self.client.force_login(self.local_admin)
        response = self.client.patch(
            reverse("authentik_api:tenant_settings"),
            data={
                "flags": {"tenants_test_flag": True},
            },
        )
        self.assertEqual(response.status_code, 200)

    def test_settings_flags_incorrect(self):
        """Test settings API"""

        class TestFlag(Flag[bool], key="tenants_test_flag"):

            default = False
            visibility = "public"

        self.client.force_login(self.local_admin)
        response = self.client.patch(
            reverse("authentik_api:tenant_settings"),
            data={
                "flags": {"tenants_test_flag": 123},
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(
            response.content,
            {"flags": ["Value for flag tenants_test_flag needs to be of type bool."]},
        )
