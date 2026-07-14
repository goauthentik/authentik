"""Test OAuth2 API"""

from json import loads
from sys import version_info
from unittest import skipUnless

from django.urls import reverse
from rest_framework.test import APITestCase

from authentik.blueprints.tests import apply_blueprint
from authentik.core.models import Application
from authentik.core.tests.utils import create_test_admin_user, create_test_cert, create_test_flow
from authentik.crypto.builder import PrivateKeyAlg
from authentik.crypto.models import CertificateKeyPair, KeyType
from authentik.lib.generators import generate_id
from authentik.providers.oauth2.models import (
    OAuth2Provider,
    RedirectURI,
    RedirectURIMatchingMode,
    ScopeMapping,
)

# A self-signed DSA keypair. authentik cannot generate DSA keys -- DSA is not offered by
# CertificateBuilder -- but one can still be imported, and DSA has no JWA signature algorithm, so
# this is the fixture for "a key type that must be rejected for JOSE". Valid until 2120.
TEST_DSA_CERT = """-----BEGIN CERTIFICATE-----
MIIERDCCA+qgAwIBAgIUBeM+I5XERv55UePOnWr7IfRPPpMwCwYJYIZIAWUDBAMC
MCkxJzAlBgNVBAMMHmRzYS5zZWxmLXNpZ25lZC5nb2F1dGhlbnRpay5pbzAgFw0y
MDAxMDEwMDAwMDBaGA8yMTIwMDEwMTAwMDAwMFowKTEnMCUGA1UEAwweZHNhLnNl
bGYtc2lnbmVkLmdvYXV0aGVudGlrLmlvMIIDRjCCAjkGByqGSM44BAEwggIsAoIB
AQDMA01NfzmEp/nhjzOMad/0cdtf9bnnoD1Em23KT4E5kaenNzlNqZoUiCq7vcaf
I0EqpaVR7ylLVOCPP3vw55/LwuuuO1Ep5CYF6XqyFBFPmRsNGjScV1XG2GBcbmIw
39Gtn5PVsXDh7eVIRmibRDScetlgYOQtpVisNKaTIqziPHJGBJU03DX1MVs2BL+a
0uWZAR3U1jKchSDmzGOOgZvAlIzn3OKQztiBBNDeSViVx9huoaRYpf6nOwTKdd/5
4Lg5Icm8NiId0r1cYcR25WiEQnTYJJp+Xxx5VmMZOPVCXqnjbG30S7CXHMCWuRAv
az6RiFM4gYDIcpwWXEu8uQTXAiEAg7eW6/Gmch0VAyoDhfx0j2vv0v+/VQtUHMy7
dwUlSD0CggEALQw11zTwbMTjrEde+I+YBcMTt0EBIgZ4hUA5YkgMh5nt7bZpQdpU
bvELG9OfFB6FZBWyha5qm44ipOZCOWq6fHAZhQZ3dOajTxfxNWQkCPOCZ7UFAOxS
Y6TYdU90VFj7o+OXKMCv8SnrTASSV8XmIvOPUze28Wn2Zlu0uAPmGmhKKBOlNGMh
tATf/CjrgunNVdFu0R+68G4++FUWhJvtPHHjeSJJksDCNzjUMy23426BWKEL4MCn
qLL5kYTmgwtAqLbNoJ+QKIjGBUxnT5wWDTlUGCmJQKr4D+VVOFqmsIUHzRhYzz+5
+8LuuF25i4deqCP1VZOMY1dMJMHwo6w+NgOCAQUAAoIBACC/yTdsZXaNU8p1neOJ
MkoEHn1IkJ5FrZWgDi1viKbTkjhG6wdBYrkGHi2yHY3Dgs1AJN/0srTWHVCtiJIK
y9GjAfprWwWBFlozXDaDim/d4ypTl81Z4agT/AE0+pV7mQC0rj5K8+TYn5j8H9uM
dmba0yzvMQLI+chR2ynlfWY2LsoYo5rKKTuIAWjeQukYobYOfo4KU4fK7iC8zMeT
HIevsfzSADnOba7wtufqlhy6yVxvmn/e5kvvVh49itN1TCH40EAcTrp+eKlSuQyR
z1gmoXdIpATy0i2B73Vavyo6CWVmiIg13nLiVwtrzITzxk7/RhGL2aZ2zT2F7Fxz
t+YwCwYJYIZIAWUDBAMCA0cAMEQCIHfkkbdUS4dH1Enyr7NRwbPGyaulZ1L2hlQs
mGqyZEw6AiAPAPjgcp5Uu0dfHlHzmVSaJRG0Xv8VROZfVIDuCVvt7w==
-----END CERTIFICATE-----"""
TEST_DSA_KEY = """-----BEGIN PRIVATE KEY-----
MIICZAIBADCCAjkGByqGSM44BAEwggIsAoIBAQDMA01NfzmEp/nhjzOMad/0cdtf
9bnnoD1Em23KT4E5kaenNzlNqZoUiCq7vcafI0EqpaVR7ylLVOCPP3vw55/Lwuuu
O1Ep5CYF6XqyFBFPmRsNGjScV1XG2GBcbmIw39Gtn5PVsXDh7eVIRmibRDScetlg
YOQtpVisNKaTIqziPHJGBJU03DX1MVs2BL+a0uWZAR3U1jKchSDmzGOOgZvAlIzn
3OKQztiBBNDeSViVx9huoaRYpf6nOwTKdd/54Lg5Icm8NiId0r1cYcR25WiEQnTY
JJp+Xxx5VmMZOPVCXqnjbG30S7CXHMCWuRAvaz6RiFM4gYDIcpwWXEu8uQTXAiEA
g7eW6/Gmch0VAyoDhfx0j2vv0v+/VQtUHMy7dwUlSD0CggEALQw11zTwbMTjrEde
+I+YBcMTt0EBIgZ4hUA5YkgMh5nt7bZpQdpUbvELG9OfFB6FZBWyha5qm44ipOZC
OWq6fHAZhQZ3dOajTxfxNWQkCPOCZ7UFAOxSY6TYdU90VFj7o+OXKMCv8SnrTASS
V8XmIvOPUze28Wn2Zlu0uAPmGmhKKBOlNGMhtATf/CjrgunNVdFu0R+68G4++FUW
hJvtPHHjeSJJksDCNzjUMy23426BWKEL4MCnqLL5kYTmgwtAqLbNoJ+QKIjGBUxn
T5wWDTlUGCmJQKr4D+VVOFqmsIUHzRhYzz+5+8LuuF25i4deqCP1VZOMY1dMJMHw
o6w+NgQiAiBFXBmn2RZR6dj4wwtUUA6ldyUh6bkKt7VMZ32gZgyOZg==
-----END PRIVATE KEY-----"""


class TestAPI(APITestCase):
    """Test api view"""

    @apply_blueprint("system/providers-oauth2.yaml")
    def setUp(self) -> None:
        self.provider: OAuth2Provider = OAuth2Provider.objects.create(
            name="test",
            authorization_flow=create_test_flow(),
            redirect_uris=[RedirectURI(RedirectURIMatchingMode.STRICT, "http://testserver")],
        )
        self.provider.property_mappings.set(ScopeMapping.objects.all())
        self.app = Application.objects.create(name="test", slug="test", provider=self.provider)
        self.user = create_test_admin_user()
        self.client.force_login(self.user)

    def set_signing_key(self, cert: CertificateKeyPair):
        return self.client.patch(
            reverse("authentik_api:oauth2provider-detail", kwargs={"pk": self.provider.pk}),
            data={"signing_key": str(cert.pk)},
        )

    def test_validate_signing_key_unsupported_type(self):
        """Test that a key type JWTAlgorithms cannot map is rejected rather than 500ing later.

        DSA is the only such type left. authentik deliberately cannot generate DSA keys, so this
        uses a checked-in keypair -- such a certificate can still reach us via import."""
        cert = CertificateKeyPair.objects.create(
            name=generate_id(),
            certificate_data=TEST_DSA_CERT,
            key_data=TEST_DSA_KEY,
        )
        self.assertEqual(cert.key_type, KeyType.DSA)
        response = self.set_signing_key(cert)
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(
            response.content,
            {
                "signing_key": [
                    "Key type DSA is not supported. Supported key types are: "
                    "RSA, Elliptic Curve, Ed25519, Ed448."
                ]
            },
        )

    def test_validate_encryption_key_unsupported_type(self):
        """Test that a non-RSA encryption key is rejected, as RSA-OAEP-256 is hardcoded"""
        cert = create_test_cert(PrivateKeyAlg.ECDSA)
        response = self.client.patch(
            reverse("authentik_api:oauth2provider-detail", kwargs={"pk": self.provider.pk}),
            data={"encryption_key": str(cert.pk)},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("encryption_key", loads(response.content))

    def test_validate_signing_key_supported_types(self):
        """Test that every key type JWTAlgorithms can map is accepted.

        Ed25519 and Ed448 both sign as EdDSA (RFC 8037)."""
        for alg in [
            PrivateKeyAlg.RSA,
            PrivateKeyAlg.ECDSA,
            PrivateKeyAlg.ED25519,
            PrivateKeyAlg.ED448,
        ]:
            with self.subTest(alg):
                response = self.set_signing_key(create_test_cert(alg))
                self.assertEqual(response.status_code, 200)

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
        self.provider.redirect_uris = [
            RedirectURI(
                RedirectURIMatchingMode.REGEX,
                "https://[\\d\\w]+.pr.test.goauthentik.io/source/oauth/callback/authentik/",
            ),
        ]
        self.provider.save()
        self.provider.refresh_from_db()
        self.assertIsNone(self.provider.launch_url)

    def test_validate_client_id(self):
        """Test redirect_uris API"""
        response = self.client.post(
            reverse("authentik_api:oauth2provider-list"),
            data={
                "name": generate_id(),
                "authorization_flow": create_test_flow().pk,
                "invalidation_flow": create_test_flow().pk,
                "client_id": "ú",
                "redirect_uris": [],
            },
        )
        self.assertJSONEqual(
            response.content,
            {"client_id": ["Client ID must consist of only ASCII characters."]},
        )

    def test_validate_client_secret(self):
        """Test redirect_uris API"""
        response = self.client.post(
            reverse("authentik_api:oauth2provider-list"),
            data={
                "name": generate_id(),
                "authorization_flow": create_test_flow().pk,
                "invalidation_flow": create_test_flow().pk,
                "client_secret": "ú",
                "redirect_uris": [],
            },
        )
        self.assertJSONEqual(
            response.content,
            {"client_secret": ["Client secret must consist of only ASCII characters."]},
        )

    def test_validate_redirect_uris(self):
        """Test redirect_uris API"""
        response = self.client.post(
            reverse("authentik_api:oauth2provider-list"),
            data={
                "name": generate_id(),
                "authorization_flow": create_test_flow().pk,
                "invalidation_flow": create_test_flow().pk,
                "redirect_uris": [
                    {"matching_mode": "strict", "url": "http://goauthentik.io"},
                    {"matching_mode": "regex", "url": "**"},
                ],
            },
        )
        self.assertJSONEqual(response.content, {"redirect_uris": ["Invalid Regex Pattern: **"]})

    def test_logout_uri_validation(self):
        """Test logout_uri API validation"""
        response = self.client.post(
            reverse("authentik_api:oauth2provider-list"),
            data={
                "name": generate_id(),
                "authorization_flow": create_test_flow().pk,
                "invalidation_flow": create_test_flow().pk,
                "redirect_uris": [
                    {"matching_mode": "strict", "url": "http://goauthentik.io"},
                ],
                "logout_uri": "invalid-url",
                "logout_method": "backchannel",
            },
        )
        self.assertEqual(response.status_code, 400)

    def test_logout_uri_create_and_retrieve(self):
        """Test creating and retrieving logout URI with method"""
        response = self.client.post(
            reverse("authentik_api:oauth2provider-list"),
            data={
                "name": generate_id(),
                "authorization_flow": create_test_flow().pk,
                "invalidation_flow": create_test_flow().pk,
                "redirect_uris": [
                    {"matching_mode": "strict", "url": "http://goauthentik.io"},
                ],
                "logout_uri": "http://goauthentik.io/logout",
                "logout_method": "backchannel",
            },
        )
        self.assertEqual(response.status_code, 201)
        provider_data = response.json()
        self.assertEqual(provider_data["logout_uri"], "http://goauthentik.io/logout")
        self.assertEqual(provider_data["logout_method"], "backchannel")

        # Test retrieving the provider
        provider_pk = provider_data["pk"]
        response = self.client.get(
            reverse("authentik_api:oauth2provider-detail", kwargs={"pk": provider_pk})
        )
        self.assertEqual(response.status_code, 200)
        retrieved_data = response.json()
        self.assertEqual(retrieved_data["logout_uri"], "http://goauthentik.io/logout")
        self.assertEqual(retrieved_data["logout_method"], "backchannel")
