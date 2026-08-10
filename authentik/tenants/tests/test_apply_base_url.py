"""Tests for the apply_base_url helper"""

from django.test import TestCase

from authentik.tenants.utils import apply_base_url, get_current_tenant


class TestApplyBaseURL(TestCase):
    """apply_base_url resolves relative URLs against the tenant's base URL"""

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
                self.assertEqual(apply_base_url(value), expected)

    def test_absolute_unchanged(self):
        """URLs that already have a scheme are returned unchanged"""
        self.set_base_url("https://authentik.company")
        for value in [
            "https://files.example.com/export.csv",
            "http://localhost:9000/if/admin/",
            "mailto:admin@authentik.company",
        ]:
            with self.subTest(value=value):
                self.assertEqual(apply_base_url(value), value)

    def test_scheme_relative(self):
        """Scheme-relative URLs adopt the base URL's scheme"""
        self.set_base_url("https://authentik.company")
        self.assertEqual(apply_base_url("//cdn.example.com/asset"), "https://cdn.example.com/asset")

    def test_no_base_url(self):
        """Without a configured base URL relative URLs are returned unchanged"""
        self.set_base_url("")
        self.assertEqual(apply_base_url("/if/admin/"), "/if/admin/")
