"""JWKS tests"""
import json

from django.urls.base import reverse
from jwt import PyJWKSet

from authentik.core.models import Application
from authentik.core.tests.utils import create_test_cert, create_test_flow
from authentik.providers.oauth2.models import OAuth2Provider
from authentik.providers.oauth2.tests.utils import OAuthTestCase


class TestJWKS(OAuthTestCase):
    """Test JWKS view"""

    def test_rs256(self):
        """Test JWKS request with RS256"""
        provider = OAuth2Provider.objects.create(
            name="test",
            client_id="test",
            authorization_flow=create_test_flow(),
            redirect_uris="http://local.invalid",
            signing_key=create_test_cert(),
        )
        app = Application.objects.create(name="test", slug="test", provider=provider)
        response = self.client.get(
            reverse("authentik_providers_oauth2:jwks", kwargs={"application_slug": app.slug})
        )
        body = json.loads(response.content.decode())
        self.assertEqual(len(body["keys"]), 1)
        PyJWKSet.from_dict(body)

    def test_hs256(self):
        """Test JWKS request with HS256"""
        provider = OAuth2Provider.objects.create(
            name="test",
            client_id="test",
            authorization_flow=create_test_flow(),
            redirect_uris="http://local.invalid",
        )
        app = Application.objects.create(name="test", slug="test", provider=provider)
        response = self.client.get(
            reverse("authentik_providers_oauth2:jwks", kwargs={"application_slug": app.slug})
        )
        self.assertJSONEqual(response.content.decode(), {})

    def test_es256(self):
        """Test JWKS request with ES256"""
        provider = OAuth2Provider.objects.create(
            name="test",
            client_id="test",
            authorization_flow=create_test_flow(),
            redirect_uris="http://local.invalid",
            signing_key=create_test_cert(use_ec_private_key=True),
        )
        app = Application.objects.create(name="test", slug="test", provider=provider)
        response = self.client.get(
            reverse("authentik_providers_oauth2:jwks", kwargs={"application_slug": app.slug})
        )
        body = json.loads(response.content.decode())
        self.assertEqual(len(body["keys"]), 1)
        PyJWKSet.from_dict(body)
