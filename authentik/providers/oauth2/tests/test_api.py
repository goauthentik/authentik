"""Test OAuth2 API"""
from json import loads
from sys import version_info
from unittest import skipUnless

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.blueprints.tests import apply_blueprint
from authentik.core.models import Application
from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.providers.oauth2.models import OAuth2Provider, ScopeMapping


class TestAPI(APITestCase):
    """Test api view"""

    @apply_blueprint("system/providers-oauth2.yaml")
    def setUp(self) -> None:
        self.provider: OAuth2Provider = OAuth2Provider.objects.create(
            name="test",
            authorization_flow=create_test_flow(),
            redirect_uris="http://testserver",
        )
        self.provider.property_mappings.set(ScopeMapping.objects.all())
        self.app = Application.objects.create(name="test", slug="test", provider=self.provider)
        self.user = create_test_admin_user()
        self.client.force_login(self.user)

    def test_preview(self):
        """Test Preview API Endpoint"""
        response = self.client.get(
            reverse("authentik_api:oauth2provider-preview-user", kwargs={"pk": self.provider.pk})
        )
        self.assertEqual(response.status_code, 200)
        body = loads(response.content.decode())["preview"]
        self.assertEqual(body["iss"], "http://testserver/application/o/test/")

    def test_setup_urls(self):
        """Test Setup URLs API Endpoint"""
        response = self.client.get(
            reverse("authentik_api:oauth2provider-setup-urls", kwargs={"pk": self.provider.pk})
        )
        self.assertEqual(response.status_code, 200)
        body = loads(response.content.decode())
        self.assertEqual(body["issuer"], "http://testserver/application/o/test/")

    # https://github.com/goauthentik/authentik/pull/5918
    @skipUnless(version_info >= (3, 11, 4), "This behaviour is only Python 3.11.4 and up")
    def test_launch_url(self):
        """Test launch_url"""
        self.provider.redirect_uris = (
            "https://[\\d\\w]+.pr.test.goauthentik.io/source/oauth/callback/authentik/\n"
        )
        self.provider.save()
        self.provider.refresh_from_db()
        self.assertIsNone(self.provider.launch_url)
