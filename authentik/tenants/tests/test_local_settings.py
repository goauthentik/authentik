"""Test Settings API"""

from django.core.management import call_command
from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.tests.utils import create_test_admin_user
from authentik.tenants.flags import Flag
from authentik.tenants.utils import get_current_tenant


class TestLocalSettingsAPI(APITestCase):
    """Test settings API"""

    def setUp(self):
        super().setUp()
        self.local_admin = create_test_admin_user()
        self.tenant = get_current_tenant()

    def tearDown(self):
        super().tearDown()
        self.tenant.flags = {}
        self.tenant.save()

    def test_settings_flags(self):
        """Test settings API"""
        self.tenant.flags = {}
        self.tenant.save()

        class _TestFlag(Flag[bool], key="tenants_test_flag_bool"):

            default = False
            visibility = "public"

        self.client.force_login(self.local_admin)
        response = self.client.patch(
            reverse("authentik_api:tenant_settings"),
            data={
                "flags": {"tenants_test_flag_bool": True},
            },
        )
        self.assertEqual(response.status_code, 200)
        self.tenant.refresh_from_db()
        self.assertEqual(self.tenant.flags["tenants_test_flag_bool"], True)

    def test_settings_flags_incorrect(self):
        """Test settings API"""
        self.tenant.flags = {}
        self.tenant.save()

        class _TestFlag(Flag[bool], key="tenants_test_flag_incorrect"):

            default = False
            visibility = "public"

        self.client.force_login(self.local_admin)
        response = self.client.patch(
            reverse("authentik_api:tenant_settings"),
            data={
                "flags": {"tenants_test_flag_incorrect": 123},
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(
            response.content,
            {"flags": ["Value for flag tenants_test_flag_incorrect needs to be of type bool."]},
        )
        self.tenant.refresh_from_db()
        self.assertEqual(self.tenant.flags, {})

    def test_settings_flags_system(self):
        """Test settings API"""
        self.tenant.flags = {}
        self.tenant.save()

        class _TestFlag(Flag[bool], key="tenants_test_flag_sys"):

            default = False
            visibility = "system"

        self.client.force_login(self.local_admin)
        response = self.client.patch(
            reverse("authentik_api:tenant_settings"),
            data={
                "flags": {"tenants_test_flag_sys": 123},
            },
        )
        self.assertEqual(response.status_code, 200)
        self.tenant.refresh_from_db()
        self.assertEqual(self.tenant.flags, {"setup": False, "tenants_test_flag_sys": False})

    def test_settings_flags_system_empty_put(self):
        """Test settings API"""
        self.tenant.flags = {}
        self.tenant.save()

        class _TestFlag(Flag[bool], key="tenants_test_flag_sys"):

            default = False
            visibility = "system"

        self.client.force_login(self.local_admin)
        response = self.client.patch(
            reverse("authentik_api:tenant_settings"),
            data={
                "flags": {},
            },
        )
        self.assertEqual(response.status_code, 200)
        self.tenant.refresh_from_db()
        self.assertEqual(self.tenant.flags, {"setup": False, "tenants_test_flag_sys": False})

    def test_command(self):
        self.tenant.flags = {}
        self.tenant.save()

        call_command("set_flag", "foo", "true")

        self.tenant.refresh_from_db()
        self.assertTrue(self.tenant.flags["foo"])
