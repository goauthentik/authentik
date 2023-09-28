"""Test tenants"""
from django.test.client import RequestFactory
from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.core.tests.utils import create_test_admin_user, create_test_tenant
from authentik.events.models import Event, EventAction
from authentik.lib.config import CONFIG
from authentik.lib.utils.time import timedelta_from_string
from authentik.tenants.api import Themes
from authentik.tenants.models import Tenant


class TestTenants(APITestCase):
    """Test tenants"""

    def test_current_tenant(self):
        """Test Current tenant API"""
        tenant = create_test_tenant()
        self.assertJSONEqual(
            self.client.get(reverse("authentik_api:tenant-current")).content.decode(),
            {
                "branding_logo": "/static/dist/assets/icons/icon_left_brand.svg",
                "branding_favicon": "/static/dist/assets/icons/icon.png",
                "branding_title": "authentik",
                "matched_domain": tenant.domain,
                "ui_footer_links": CONFIG.get("footer_links"),
                "ui_theme": Themes.AUTOMATIC,
                "default_locale": "",
            },
        )

    def test_tenant_subdomain(self):
        """Test Current tenant API"""
        Tenant.objects.all().delete()
        Tenant.objects.create(domain="bar.baz", branding_title="custom")
        self.assertJSONEqual(
            self.client.get(
                reverse("authentik_api:tenant-current"), HTTP_HOST="foo.bar.baz"
            ).content.decode(),
            {
                "branding_logo": "/static/dist/assets/icons/icon_left_brand.svg",
                "branding_favicon": "/static/dist/assets/icons/icon.png",
                "branding_title": "custom",
                "matched_domain": "bar.baz",
                "ui_footer_links": CONFIG.get("footer_links"),
                "ui_theme": Themes.AUTOMATIC,
                "default_locale": "",
            },
        )

    def test_fallback(self):
        """Test fallback tenant"""
        Tenant.objects.all().delete()
        self.assertJSONEqual(
            self.client.get(reverse("authentik_api:tenant-current")).content.decode(),
            {
                "branding_logo": "/static/dist/assets/icons/icon_left_brand.svg",
                "branding_favicon": "/static/dist/assets/icons/icon.png",
                "branding_title": "authentik",
                "matched_domain": "fallback",
                "ui_footer_links": CONFIG.get("footer_links"),
                "ui_theme": Themes.AUTOMATIC,
                "default_locale": "",
            },
        )

    def test_event_retention(self):
        """Test tenant's event retention"""
        tenant = Tenant.objects.create(
            domain="foo",
            default=True,
            branding_title="custom",
            event_retention="weeks=3",
        )
        factory = RequestFactory()
        request = factory.get("/")
        request.tenant = tenant
        event = Event.new(action=EventAction.SYSTEM_EXCEPTION, message="test").from_http(request)
        self.assertEqual(event.expires.day, (event.created + timedelta_from_string("weeks=3")).day)
        self.assertEqual(
            event.expires.month,
            (event.created + timedelta_from_string("weeks=3")).month,
        )
        self.assertEqual(
            event.expires.year, (event.created + timedelta_from_string("weeks=3")).year
        )

    def test_create_default_multiple(self):
        """Test attempted creation of multiple default tenants"""
        Tenant.objects.create(
            domain="foo",
            default=True,
            branding_title="custom",
            event_retention="weeks=3",
        )
        user = create_test_admin_user()
        self.client.force_login(user)
        response = self.client.post(
            reverse("authentik_api:tenant-list"), data={"domain": "bar", "default": True}
        )
        self.assertEqual(response.status_code, 400)
