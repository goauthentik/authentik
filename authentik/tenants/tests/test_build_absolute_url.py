"""Tests for the build_absolute_url helper"""

from django.test import TestCase

from authentik.tenants.utils import build_absolute_url, get_current_tenant


class TestBuildAbsoluteURL(TestCase):
    """build_absolute_url resolves relative URLs against the tenant's base URL"""

    def set_base_url(self, value: str):
        tenant = get_current_tenant()
        tenant.base_url = value
        tenant.save()

    def test_relative(self):
        """Relative URLs are prefixed with the configured base URL"""
        self.set_base_url("https://authentik.company")
        cases = {
            "/if/admin/#/core/applications/app": (
                "https://authentik.company/if/admin/#/core/applications/app"
            ),
            "if/user/": "https://authentik.company/if/user/",
            "": "",
        }
        for value, expected in cases.items():
            with self.subTest(value=value):
                self.assertEqual(build_absolute_url(value), expected)

    def test_absolute_unchanged(self):
        """URLs that already have a scheme or host are returned unchanged"""
        self.set_base_url("https://authentik.company")
        for value in [
            "https://files.example.com/export.csv",
            "http://localhost:9000/if/admin/",
            "//cdn.example.com/asset",
            "mailto:admin@authentik.company",
        ]:
            with self.subTest(value=value):
                self.assertEqual(build_absolute_url(value), value)

    def test_no_base_url(self):
        """Without a configured base URL relative URLs are returned unchanged"""
        self.set_base_url("")
        self.assertEqual(build_absolute_url("/if/admin/"), "/if/admin/")
