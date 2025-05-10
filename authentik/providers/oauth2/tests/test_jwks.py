"""JWKS tests"""

import base64
import json

from cryptography.hazmat.backends import default_backend
from cryptography.x509 import load_der_x509_certificate
from django.urls.base import reverse
from jwt import PyJWKSet

from authentik.core.models import Application
from authentik.core.tests.utils import create_test_cert, create_test_flow
from authentik.crypto.builder import PrivateKeyAlg
from authentik.crypto.generators import generate_id
from authentik.crypto.models import CertificateKeyPair
from authentik.providers.oauth2.models import OAuth2Provider, RedirectURI, RedirectURIMatchingMode
from authentik.providers.oauth2.tests.utils import OAuthTestCase

TEST_CORDS_CERT = """
-----BEGIN CERTIFICATE-----
MIIB6jCCAZCgAwIBAgIRAOsdE3N7zETzs+7shTXGj5wwCgYIKoZIzj0EAwIwHjEc
MBoGA1UEAwwTYXV0aGVudGlrIDIwMjIuMTIuMjAeFw0yMzAxMTYyMjU2MjVaFw0y
NDAxMTIyMjU2MjVaMHgxTDBKBgNVBAMMQ0NsbDR2TzFJSGxvdFFhTGwwMHpES2tM
WENYdzRPUFF2eEtZN1NrczAuc2VsZi1zaWduZWQuZ29hdXRoZW50aWsuaW8xEjAQ
BgNVBAoMCWF1dGhlbnRpazEUMBIGA1UECwwLU2VsZi1zaWduZWQwWTATBgcqhkjO
PQIBBggqhkjOPQMBBwNCAAQAwOGam7AKOi5LKmb9lK1rAzA2JTppqrFiIaUdjqmH
ZICJP00Wt0dfqOtEjgMEv1Hhu1DmKZn2ehvpxwPSzBr5o1UwUzBRBgNVHREBAf8E
RzBFgkNCNkw4YlI0UldJRU42NUZLamdUTzV1YmRvNUZWdkpNS2lxdjFZeTRULnNl
bGYtc2lnbmVkLmdvYXV0aGVudGlrLmlvMAoGCCqGSM49BAMCA0gAMEUCIC/JAfnl
uC30ihqepbiMCaTaPMbL8Ka2Lk92IYfMhf46AiEAz9Kmv6HF2D4MK54iwhz2WqvF
8vo+OiGdTQ1Qoj7fgYU=
-----END CERTIFICATE-----
"""
TEST_CORDS_KEY = """
-----BEGIN EC PRIVATE KEY-----
MHcCAQEEIKy6mPLJc5v71InMMvYaxyXI3xXpwQTPLyAYWVFnZHVioAoGCCqGSM49
AwEHoUQDQgAEAMDhmpuwCjouSypm/ZStawMwNiU6aaqxYiGlHY6ph2SAiT9NFrdH
X6jrRI4DBL9R4btQ5imZ9nob6ccD0swa+Q==
-----END EC PRIVATE KEY-----
"""


class TestJWKS(OAuthTestCase):
    """Test JWKS view"""

    def test_rs256(self):
        """Test JWKS request with RS256"""
        provider = OAuth2Provider.objects.create(
            name="test",
            client_id="test",
            authorization_flow=create_test_flow(),
            redirect_uris=[RedirectURI(RedirectURIMatchingMode.STRICT, "http://local.invalid")],
            signing_key=create_test_cert(),
        )
        app = Application.objects.create(name="test", slug="test", provider=provider)
        response = self.client.get(
            reverse("authentik_providers_oauth2:jwks", kwargs={"application_slug": app.slug})
        )
        body = json.loads(response.content.decode())
        self.assertEqual(len(body["keys"]), 1)
        PyJWKSet.from_dict(body)
        key = body["keys"][0]
        load_der_x509_certificate(base64.b64decode(key["x5c"][0]), default_backend()).public_key()

    def test_hs256(self):
        """Test JWKS request with HS256"""
        provider = OAuth2Provider.objects.create(
            name="test",
            client_id="test",
            authorization_flow=create_test_flow(),
            redirect_uris=[RedirectURI(RedirectURIMatchingMode.STRICT, "http://local.invalid")],
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
            redirect_uris=[RedirectURI(RedirectURIMatchingMode.STRICT, "http://local.invalid")],
            signing_key=create_test_cert(PrivateKeyAlg.ECDSA),
        )
        app = Application.objects.create(name="test", slug="test", provider=provider)
        response = self.client.get(
            reverse("authentik_providers_oauth2:jwks", kwargs={"application_slug": app.slug})
        )
        body = json.loads(response.content.decode())
        self.assertEqual(len(body["keys"]), 1)
        PyJWKSet.from_dict(body)

    def test_enc(self):
        """Test with JWE"""
        provider = OAuth2Provider.objects.create(
            name="test",
            client_id="test",
            authorization_flow=create_test_flow(),
            redirect_uris=[RedirectURI(RedirectURIMatchingMode.STRICT, "http://local.invalid")],
            signing_key=create_test_cert(PrivateKeyAlg.ECDSA),
            encryption_key=create_test_cert(PrivateKeyAlg.ECDSA),
        )
        app = Application.objects.create(name="test", slug="test", provider=provider)
        response = self.client.get(
            reverse("authentik_providers_oauth2:jwks", kwargs={"application_slug": app.slug})
        )
        body = json.loads(response.content.decode())
        self.assertEqual(len(body["keys"]), 2)
        PyJWKSet.from_dict(body)

    def test_ecdsa_coords_mismatched(self):
        """Test JWKS request with ES256"""
        cert = CertificateKeyPair.objects.create(
            name=generate_id(),
            key_data=TEST_CORDS_KEY,
            certificate_data=TEST_CORDS_CERT,
        )
        provider = OAuth2Provider.objects.create(
            name="test",
            client_id="test",
            authorization_flow=create_test_flow(),
            redirect_uris=[RedirectURI(RedirectURIMatchingMode.STRICT, "http://local.invalid")],
            signing_key=cert,
        )
        app = Application.objects.create(name="test", slug="test", provider=provider)
        response = self.client.get(
            reverse("authentik_providers_oauth2:jwks", kwargs={"application_slug": app.slug})
        )
        body = json.loads(response.content.decode())
        self.assertEqual(len(body["keys"]), 1)
        PyJWKSet.from_dict(body)
