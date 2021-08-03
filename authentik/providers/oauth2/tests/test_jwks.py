"""JWKS tests"""
import json

from django.test import RequestFactory
from django.urls.base import reverse
from django.utils.encoding import force_str

from authentik.core.models import Application
from authentik.crypto.models import CertificateKeyPair
from authentik.flows.models import Flow
from authentik.providers.oauth2.models import OAuth2Provider
from authentik.providers.oauth2.tests.utils import OAuthTestCase


class TestJWKS(OAuthTestCase):
    """Test JWKS view"""

    def setUp(self) -> None:
        super().setUp()
        self.factory = RequestFactory()

    def test_rs256(self):
        """Test JWKS request with RS256"""
        provider = OAuth2Provider.objects.create(
            name="test",
            client_id="test",
            authorization_flow=Flow.objects.first(),
            redirect_uris="http://local.invalid",
            rsa_key=CertificateKeyPair.objects.first(),
        )
        app = Application.objects.create(name="test", slug="test", provider=provider)
        response = self.client.get(
            reverse("authentik_providers_oauth2:jwks", kwargs={"application_slug": app.slug})
        )
        body = json.loads(force_str(response.content))
        self.assertEqual(len(body["keys"]), 1)

    def test_hs256(self):
        """Test JWKS request with HS256"""
        provider = OAuth2Provider.objects.create(
            name="test",
            client_id="test",
            authorization_flow=Flow.objects.first(),
            redirect_uris="http://local.invalid",
        )
        app = Application.objects.create(name="test", slug="test", provider=provider)
        response = self.client.get(
            reverse("authentik_providers_oauth2:jwks", kwargs={"application_slug": app.slug})
        )
        self.assertJSONEqual(force_str(response.content), {})
