"""Test brands"""

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.brands.api import Themes
from authentik.brands.models import Brand
from authentik.core.tests.utils import create_test_admin_user, create_test_brand


class TestBrands(APITestCase):
    """Test brands"""

    def test_current_brand(self):
        """Test Current brand API"""
        brand = create_test_brand()
        self.assertJSONEqual(
            self.client.get(reverse("authentik_api:brand-current")).content.decode(),
            {
                "branding_logo": "/static/dist/assets/icons/icon_left_brand.svg",
                "branding_favicon": "/static/dist/assets/icons/icon.png",
                "branding_title": "authentik",
                "matched_domain": brand.domain,
                "ui_footer_links": [],
                "ui_theme": Themes.AUTOMATIC,
                "default_locale": "",
            },
        )

    def test_brand_subdomain(self):
        """Test Current brand API"""
        Brand.objects.all().delete()
        Brand.objects.create(domain="bar.baz", branding_title="custom")
        self.assertJSONEqual(
            self.client.get(
                reverse("authentik_api:brand-current"), HTTP_HOST="foo.bar.baz"
            ).content.decode(),
            {
                "branding_logo": "/static/dist/assets/icons/icon_left_brand.svg",
                "branding_favicon": "/static/dist/assets/icons/icon.png",
                "branding_title": "custom",
                "matched_domain": "bar.baz",
                "ui_footer_links": [],
                "ui_theme": Themes.AUTOMATIC,
                "default_locale": "",
            },
        )

    def test_fallback(self):
        """Test fallback brand"""
        Brand.objects.all().delete()
        self.assertJSONEqual(
            self.client.get(reverse("authentik_api:brand-current")).content.decode(),
            {
                "branding_logo": "/static/dist/assets/icons/icon_left_brand.svg",
                "branding_favicon": "/static/dist/assets/icons/icon.png",
                "branding_title": "authentik",
                "matched_domain": "fallback",
                "ui_footer_links": [],
                "ui_theme": Themes.AUTOMATIC,
                "default_locale": "",
            },
        )

    def test_create_default_multiple(self):
        """Test attempted creation of multiple default brands"""
        Brand.objects.create(
            domain="foo",
            default=True,
            branding_title="custom",
        )
        user = create_test_admin_user()
        self.client.force_login(user)
        response = self.client.post(
            reverse("authentik_api:brand-list"), data={"domain": "bar", "default": True}
        )
        self.assertEqual(response.status_code, 400)
