"""Tests for the base_url setting's admin API surface"""

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.tests.utils import create_test_admin_user
from authentik.tenants.utils import get_current_tenant


class TestBaseURLSettings(APITestCase):
    """base_url read and written through the admin settings and system-info APIs"""

    def setUp(self):
        super().setUp()
        self.tenant = get_current_tenant()
        self.tenant.base_url = ""
        self.tenant.save()
        self.client.force_login(create_test_admin_user())

    def test_settings_roundtrip(self):
        """base_url can be written and read back through the settings API"""
        response = self.client.patch(
            reverse("authentik_api:tenant_settings"),
            data={"base_url": "https://authentik.company"},
        )
        self.assertEqual(response.status_code, 200)
        self.tenant.refresh_from_db()
        self.assertEqual(self.tenant.base_url, "https://authentik.company")

    def test_settings_rejects_invalid(self):
        """A value that is not a URL is rejected"""
        response = self.client.patch(
            reverse("authentik_api:tenant_settings"),
            data={"base_url": "not-a-url"},
        )
        self.assertEqual(response.status_code, 400)

    def test_settings_normalizes_trailing_slash(self):
        """A trailing slash is stripped when saving through the settings API"""
        response = self.client.patch(
            reverse("authentik_api:tenant_settings"),
            data={"base_url": "https://authentik.company/"},
        )
        self.assertEqual(response.status_code, 200)
        self.tenant.refresh_from_db()
        self.assertEqual(self.tenant.base_url, "https://authentik.company")

    def test_system_info_exposes_base_url(self):
        """The admin system info endpoint exposes the configured base_url"""
        self.tenant.base_url = "https://info.example.com"
        self.tenant.save()
        response = self.client.get(reverse("authentik_api:admin_system"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["base_url"], "https://info.example.com")
