"""Test brands"""

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.brands.api import Themes
from authentik.brands.models import Brand, BrandPolicy
from authentik.core.models import Application
from authentik.core.tests.utils import create_test_admin_user, create_test_brand
from authentik.lib.generators import generate_id
from authentik.policies.dummy.models import DummyPolicy
from authentik.policies.models import PolicyBinding
from authentik.providers.oauth2.models import OAuth2Provider
from authentik.providers.saml.models import SAMLProvider


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
                "branding_custom_css": "",
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
                "branding_custom_css": "",
                "matched_domain": "bar.baz",
                "ui_footer_links": [],
                "ui_theme": Themes.AUTOMATIC,
                "default_locale": "",
            },
        )

    def test_brand_subdomain_same_suffix(self):
        """Test Current brand API"""
        Brand.objects.all().delete()
        Brand.objects.create(domain="bar.baz", branding_title="custom")
        Brand.objects.create(domain="foo.bar.baz", branding_title="custom")
        self.assertJSONEqual(
            self.client.get(
                reverse("authentik_api:brand-current"), HTTP_HOST="foo.bar.baz"
            ).content.decode(),
            {
                "branding_logo": "/static/dist/assets/icons/icon_left_brand.svg",
                "branding_favicon": "/static/dist/assets/icons/icon.png",
                "branding_title": "custom",
                "branding_custom_css": "",
                "matched_domain": "foo.bar.baz",
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
                "branding_custom_css": "",
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
                "branding_favicon": "https://goauthentik.io/img/icon.png",
                "branding_title": "authentik",
                "branding_custom_css": "",
                "matched_domain": brand.domain,
                "ui_footer_links": [],
                "ui_theme": Themes.AUTOMATIC,
                "default_locale": "",
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


class TestBrandPolicy(APITestCase):
    def setUp(self):
        self.admin = create_test_admin_user()
        self.client.force_login(self.admin)

        self.response_code = 400
        self.brand: Brand = create_test_brand()
        self.brand_policy: BrandPolicy = BrandPolicy.objects.create(
            name=generate_id(),
            brand=self.brand,
            path="/api/v3/rbac/permissions/",
            failure_http_status_code=self.response_code,
        )
        self.true_policy: DummyPolicy = DummyPolicy.objects.create(
            name=generate_id(), result=True, wait_min=1, wait_max=2
        )
        self.false_policy: DummyPolicy = DummyPolicy.objects.create(
            name=generate_id(), result=False, wait_min=1, wait_max=2
        )

    def test_brand_policy_success(self):
        """Test BrandPolicy success"""
        PolicyBinding.objects.create(target=self.brand_policy, policy=self.true_policy, order=0)

        response = self.client.get(reverse("authentik_api:permission-list"))

        self.assertEqual(response.status_code, 200)

    def test_brand_policy_failure(self):
        """Test BrandPolicy failure"""
        response_code = 451
        response_text = "The temperature at which book-paper catches fire and burns..."
        self.brand_policy.failure_http_status_code = response_code
        self.brand_policy.failure_response = response_text
        self.brand_policy.save()
        PolicyBinding.objects.create(target=self.brand_policy, policy=self.false_policy, order=0)

        response = self.client.get(reverse("authentik_api:permission-list"))

        self.assertEqual(response.status_code, response_code)
        self.assertEqual(response.content.decode(), response_text)

    def test_brand_policy_failure_json(self):
        """Test BrandPolicy failure JSON"""
        response_code = 451
        response_text = (
            '{ "Fahrenheit 451": "The temperature at which book-paper catches fire and burns..." }'
        )
        self.brand_policy.failure_http_status_code = response_code
        self.brand_policy.failure_response = response_text
        self.brand_policy.save()
        PolicyBinding.objects.create(target=self.brand_policy, policy=self.false_policy, order=0)

        response = self.client.get(reverse("authentik_api:permission-list"))

        self.assertEqual(response.status_code, response_code)
        self.assertJSONEqual(response.content, response_text)
