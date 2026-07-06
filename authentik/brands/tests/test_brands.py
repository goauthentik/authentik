"""Test brands"""

from json import loads

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.blueprints.tests import apply_blueprint
from authentik.brands.models import Brand
from authentik.core.models import Application
from authentik.core.tests.utils import create_test_admin_user, create_test_brand
from authentik.lib.generators import generate_id
from authentik.providers.oauth2.models import OAuth2Provider
from authentik.providers.saml.models import SAMLProvider
from authentik.tenants.flags import Flag


class TestBrands(APITestCase):
    """Test brands"""

    def setUp(self):
        super().setUp()
        self.default_flags = {}
        for flag in Flag.available(visibility="public"):
            self.default_flags[flag().key] = flag.get()
        Brand.objects.all().delete()

    def test_current_brand(self):
        """Test Current brand API"""
        brand = create_test_brand()
        self.assertJSONEqual(
            self.client.get(reverse("authentik_api:brand-current")).content.decode(),
            {
                "branding_logo": "/static/dist/assets/icons/icon_left_brand.svg",
                "branding_logo_themed_urls": None,
                "branding_favicon": "/static/dist/assets/icons/icon.png",
                "branding_favicon_themed_urls": None,
                "branding_title": "authentik",
                "branding_custom_css": "",
                "matched_domain": brand.domain,
                "ui_footer_links": [],
                "ui_theme": "automatic",
                "default_locale": "",
                "flags": self.default_flags,
            },
        )

    def test_brand_subdomain(self):
        """Test Current brand API"""
        Brand.objects.create(domain="bar.baz", branding_title="custom")
        self.assertJSONEqual(
            self.client.get(
                reverse("authentik_api:brand-current"), HTTP_HOST="foo.bar.baz"
            ).content.decode(),
            {
                "branding_logo": "/static/dist/assets/icons/icon_left_brand.svg",
                "branding_logo_themed_urls": None,
                "branding_favicon": "/static/dist/assets/icons/icon.png",
                "branding_favicon_themed_urls": None,
                "branding_title": "custom",
                "branding_custom_css": "",
                "matched_domain": "bar.baz",
                "ui_footer_links": [],
                "ui_theme": "automatic",
                "default_locale": "",
                "flags": self.default_flags,
            },
        )

    def test_fallback(self):
        """Test fallback brand"""
        self.assertJSONEqual(
            self.client.get(reverse("authentik_api:brand-current")).content.decode(),
            {
                "branding_logo": "/static/dist/assets/icons/icon_left_brand.svg",
                "branding_logo_themed_urls": None,
                "branding_favicon": "/static/dist/assets/icons/icon.png",
                "branding_favicon_themed_urls": None,
                "branding_title": "authentik",
                "branding_custom_css": "",
                "matched_domain": "fallback",
                "ui_footer_links": [],
                "ui_theme": "automatic",
                "default_locale": "",
                "flags": self.default_flags,
            },
        )

    @apply_blueprint("default/default-brand.yaml")
    def test_blueprint(self):
        """Test Current brand API"""
        response = loads(self.client.get(reverse("authentik_api:brand-current")).content.decode())
        response.pop("flow_authentication", None)
        response.pop("flow_invalidation", None)
        response.pop("flow_user_settings", None)
        self.assertEqual(
            response,
            {
                "branding_logo": "/static/dist/assets/icons/icon_left_brand.svg",
                "branding_logo_themed_urls": None,
                "branding_favicon": "/static/dist/assets/icons/icon.png",
                "branding_favicon_themed_urls": None,
                "branding_title": "authentik",
                "branding_custom_css": "",
                "matched_domain": "authentik-default",
                "ui_footer_links": [],
                "ui_theme": "automatic",
                "default_locale": "",
                "flags": self.default_flags,
            },
        )

    @apply_blueprint("default/default-brand.yaml")
    def test_blueprint_with_other_brand(self):
        """Test Current brand API"""
        Brand.objects.create(domain="bar.baz", branding_title="custom")
        response = loads(self.client.get(reverse("authentik_api:brand-current")).content.decode())
        response.pop("flow_authentication", None)
        response.pop("flow_invalidation", None)
        response.pop("flow_user_settings", None)
        self.assertEqual(
            response,
            {
                "branding_logo": "/static/dist/assets/icons/icon_left_brand.svg",
                "branding_logo_themed_urls": None,
                "branding_favicon": "/static/dist/assets/icons/icon.png",
                "branding_favicon_themed_urls": None,
                "branding_title": "authentik",
                "branding_custom_css": "",
                "matched_domain": "authentik-default",
                "ui_footer_links": [],
                "ui_theme": "automatic",
                "default_locale": "",
                "flags": self.default_flags,
            },
        )
        self.assertJSONEqual(
            self.client.get(
                reverse("authentik_api:brand-current"), HTTP_HOST="foo.bar.baz"
            ).content.decode(),
            {
                "branding_logo": "/static/dist/assets/icons/icon_left_brand.svg",
                "branding_logo_themed_urls": None,
                "branding_favicon": "/static/dist/assets/icons/icon.png",
                "branding_favicon_themed_urls": None,
                "branding_title": "custom",
                "branding_custom_css": "",
                "matched_domain": "bar.baz",
                "ui_footer_links": [],
                "ui_theme": "automatic",
                "default_locale": "",
                "flags": self.default_flags,
            },
        )

    def test_brand_subdomain_same_suffix(self):
        """Test Current brand API"""
        Brand.objects.create(domain="bar.baz", branding_title="custom-weak")
        Brand.objects.create(domain="foo.bar.baz", branding_title="custom-strong")
        self.assertJSONEqual(
            self.client.get(
                reverse("authentik_api:brand-current"), HTTP_HOST="foo.bar.baz"
            ).content.decode(),
            {
                "branding_logo": "/static/dist/assets/icons/icon_left_brand.svg",
                "branding_logo_themed_urls": None,
                "branding_favicon": "/static/dist/assets/icons/icon.png",
                "branding_favicon_themed_urls": None,
                "branding_title": "custom-strong",
                "branding_custom_css": "",
                "matched_domain": "foo.bar.baz",
                "ui_footer_links": [],
                "ui_theme": "automatic",
                "default_locale": "",
                "flags": self.default_flags,
            },
        )

    def test_brand_subdomain_other_suffix(self):
        """Test Current brand API"""
        Brand.objects.create(domain="bar.baz", branding_title="custom-weak")
        Brand.objects.create(domain="foo.bar.baz", branding_title="custom-strong")
        self.assertJSONEqual(
            self.client.get(
                reverse("authentik_api:brand-current"), HTTP_HOST="other.bar.baz"
            ).content.decode(),
            {
                "branding_logo": "/static/dist/assets/icons/icon_left_brand.svg",
                "branding_logo_themed_urls": None,
                "branding_favicon": "/static/dist/assets/icons/icon.png",
                "branding_favicon_themed_urls": None,
                "branding_title": "custom-weak",
                "branding_custom_css": "",
                "matched_domain": "bar.baz",
                "ui_footer_links": [],
                "ui_theme": "automatic",
                "default_locale": "",
                "flags": self.default_flags,
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

    def test_webfinger_no_app(self):
        """Test Webfinger"""
        create_test_brand()
        self.assertJSONEqual(
            self.client.get(reverse("authentik_brands:webfinger")).content.decode(), {}
        )

    def test_webfinger_not_supported(self):
        """Test Webfinger"""
        brand = create_test_brand()
        provider = SAMLProvider.objects.create(
            name=generate_id(),
        )
        app = Application.objects.create(name=generate_id(), slug=generate_id(), provider=provider)
        brand.default_application = app
        brand.save()
        self.assertJSONEqual(
            self.client.get(reverse("authentik_brands:webfinger")).content.decode(), {}
        )

    def test_webfinger_oidc(self):
        """Test Webfinger"""
        brand = create_test_brand()
        provider = OAuth2Provider.objects.create(
            name=generate_id(),
        )
        app = Application.objects.create(name=generate_id(), slug=generate_id(), provider=provider)
        brand.default_application = app
        brand.save()
        self.assertJSONEqual(
            self.client.get(reverse("authentik_brands:webfinger")).content.decode(),
            {
                "links": [
                    {
                        "href": f"http://testserver/application/o/{app.slug}/",
                        "rel": "http://openid.net/specs/connect/1.0/issuer",
                    }
                ],
                "subject": None,
            },
        )

    def test_branding_url(self):
        """Test branding attributes return correct values"""
        brand = create_test_brand()
        brand.branding_default_flow_background = "https://goauthentik.io/img/icon.png"
        brand.branding_favicon = "https://goauthentik.io/img/icon.png"
        brand.branding_logo = "https://goauthentik.io/img/icon.png"
        brand.save()
        self.assertEqual(
            brand.branding_default_flow_background_url(), "https://goauthentik.io/img/icon.png"
        )
        self.assertJSONEqual(
            self.client.get(reverse("authentik_api:brand-current")).content.decode(),
            {
                "branding_logo": "https://goauthentik.io/img/icon.png",
                "branding_logo_themed_urls": None,
                "branding_favicon": "https://goauthentik.io/img/icon.png",
                "branding_favicon_themed_urls": None,
                "branding_title": "authentik",
                "branding_custom_css": "",
                "matched_domain": brand.domain,
                "ui_footer_links": [],
                "ui_theme": "automatic",
                "default_locale": "",
                "flags": self.default_flags,
            },
        )

    def test_custom_css(self):
        """Test custom_css"""
        brand = create_test_brand()
        brand.branding_custom_css = """* {
            font-family: "Foo bar";
        }"""
        brand.save()
        res = self.client.get(reverse("authentik_core:if-user"))
        self.assertEqual(res.status_code, 200)
        self.assertIn(brand.branding_custom_css, res.content.decode())
