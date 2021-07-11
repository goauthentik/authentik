"""Test tenants"""
from django.test import TestCase
from django.urls import reverse
from django.utils.encoding import force_str

from authentik.lib.config import CONFIG
from authentik.tenants.models import Tenant


class TestTenants(TestCase):
    """Test tenants"""

    def test_current_tenant(self):
        """Test Current tenant API"""
        self.assertJSONEqual(
            force_str(self.client.get(reverse("authentik_api:tenant-current")).content),
            {
                "branding_logo": "/static/dist/assets/icons/icon_left_brand.svg",
                "branding_favicon": "/static/dist/assets/icons/icon.png",
                "branding_title": "authentik",
                "matched_domain": "authentik-default",
                "ui_footer_links": CONFIG.y("footer_links"),
                "flow_authentication": "default-authentication-flow",
                "flow_invalidation": "default-invalidation-flow",
            },
        )

    def test_tenant_subdomain(self):
        """Test Current tenant API"""
        Tenant.objects.all().delete()
        Tenant.objects.create(domain="bar.baz", branding_title="custom")
        self.assertJSONEqual(
            force_str(
                self.client.get(
                    reverse("authentik_api:tenant-current"), HTTP_HOST="foo.bar.baz"
                ).content
            ),
            {
                "branding_logo": "/static/dist/assets/icons/icon_left_brand.svg",
                "branding_favicon": "/static/dist/assets/icons/icon.png",
                "branding_title": "custom",
                "matched_domain": "bar.baz",
                "ui_footer_links": CONFIG.y("footer_links"),
            },
        )

    def test_fallback(self):
        """Test fallback tenant"""
        Tenant.objects.all().delete()
        self.assertJSONEqual(
            force_str(self.client.get(reverse("authentik_api:tenant-current")).content),
            {
                "branding_logo": "/static/dist/assets/icons/icon_left_brand.svg",
                "branding_favicon": "/static/dist/assets/icons/icon.png",
                "branding_title": "authentik",
                "matched_domain": "fallback",
                "ui_footer_links": CONFIG.y("footer_links"),
            },
        )
