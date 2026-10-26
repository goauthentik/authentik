"""OpenID Type tests"""

import time
from unittest.mock import patch

from cryptography.exceptions import UnsupportedAlgorithm
from cryptography.hazmat.primitives.asymmetric.mldsa import MLDSA44PrivateKey
from django.test import RequestFactory, TestCase
from jwt import encode
from requests_mock import Mocker

from authentik.core.tests.utils import create_test_cert
from authentik.crypto.builder import PrivateKeyAlg
from authentik.crypto.models import CertificateKeyPair
from authentik.lib.generators import generate_id
from authentik.lib.jwt_mldsa import MLDSAAlgorithm
from authentik.providers.oauth2.views.jwks import JWKSView
from authentik.sources.oauth.models import OAuthSource
from authentik.sources.oauth.types.oidc import OpenIDConnectOAuth2Callback, OpenIDConnectType

# https://connect2id.com/products/server/docs/api/userinfo
OPENID_USER = {
    "sub": "83692",
    "name": "Alice Adams",
    "email": "alice@example.com",
    "department": "Engineering",
    "birthdate": "1975-12-31",
    "nickname": "foo",
}


def mldsa_jwk(cert: CertificateKeyPair) -> dict:
    """Public AKP JWK (RFC 9964) for an ML-DSA certificate, as an upstream IdP would publish it"""
    jwk = MLDSAAlgorithm.to_jwk(cert.private_key.public_key(), as_dict=True)
    jwk["kid"] = cert.kid
    jwk["use"] = "sig"
    return jwk


class TestTypeOpenID(TestCase):
    """OAuth Source tests"""

    def setUp(self):
        self.source = OAuthSource.objects.create(
            name="test",
            slug="test",
            provider_type="openidconnect",
            authorization_url="",
            profile_url="http://localhost/userinfo",
            consumer_key="",
        )
        self.factory = RequestFactory()

    def test_enroll_context(self):
        """Test OpenID Enrollment context"""
        ak_context = OpenIDConnectType().get_base_user_properties(
            source=self.source, info=OPENID_USER
        )
        self.assertEqual(ak_context["username"], OPENID_USER["nickname"])
        self.assertEqual(ak_context["email"], OPENID_USER["email"])
        self.assertEqual(ak_context["name"], OPENID_USER["name"])

    @Mocker()
    def test_userinfo(self, mock: Mocker):
        """Test userinfo API call"""
        mock.get("http://localhost/userinfo", json=OPENID_USER)
        token = generate_id()
        OpenIDConnectOAuth2Callback(request=self.factory.get("/")).get_client(
            self.source
        ).get_profile_info(
            {
                "token_type": "foo",
                "access_token": token,
            }
        )
        self.assertEqual(mock.last_request.query, "")
        self.assertEqual(mock.last_request.headers["Authorization"], f"foo {token}")

    @Mocker()
    def test_userinfo_jwt(self, mock: Mocker):
        """Test id_token fallback when profile_url is empty"""
        jwks_cert = create_test_cert()
        client_id = generate_id()
        self.source.profile_url = ""
        self.source.consumer_key = client_id
        self.source.oidc_jwks = {"keys": [JWKSView.get_jwk_for_key(jwks_cert, "sig")]}
        self.source.save()
        token = generate_id()
        now = int(time.time())
        id_token_payload = {
            "iss": "https://example.com",
            "sub": OPENID_USER["sub"],
            "aud": client_id,
            "exp": now + 3600,
            "iat": now,
            "name": OPENID_USER["name"],
            "email": OPENID_USER["email"],
            "nickname": OPENID_USER["nickname"],
        }
        profile = (
            OpenIDConnectOAuth2Callback(request=self.factory.get("/"))
            .get_client(self.source)
            .get_profile_info(
                {
                    "token_type": "Bearer",
                    "access_token": token,
                    "id_token": encode(
                        id_token_payload,
                        key=jwks_cert.private_key,
                        algorithm="RS256",
                        headers={"kid": self.source.oidc_jwks["keys"][0]["kid"]},
                    ),
                }
            )
        )
        self.assertEqual(profile["sub"], OPENID_USER["sub"])
        self.assertEqual(profile["name"], OPENID_USER["name"])
        self.assertEqual(profile["email"], OPENID_USER["email"])
        self.assertEqual(profile["aud"], client_id)
        self.assertEqual(profile["iss"], "https://example.com")

    @Mocker()
    def test_userinfo_jwt_mldsa(self, mock: Mocker):
        """Test id_token fallback with an ML-DSA (RFC 9964) signed id_token"""
        jwks_cert = create_test_cert(PrivateKeyAlg.MLDSA44)
        client_id = generate_id()
        self.source.profile_url = ""
        self.source.consumer_key = client_id
        self.source.oidc_jwks = {"keys": [mldsa_jwk(jwks_cert)]}
        self.source.save()
        self.assertEqual(self.source.oidc_jwks["keys"][0]["kty"], "AKP")
        now = int(time.time())
        id_token_payload = {
            "iss": "https://example.com",
            "sub": OPENID_USER["sub"],
            "aud": client_id,
            "exp": now + 3600,
            "iat": now,
            "email": OPENID_USER["email"],
        }
        profile = (
            OpenIDConnectOAuth2Callback(request=self.factory.get("/"))
            .get_client(self.source)
            .get_profile_info(
                {
                    "token_type": "Bearer",
                    "access_token": generate_id(),
                    "id_token": encode(
                        id_token_payload,
                        key=jwks_cert.private_key,
                        algorithm="ML-DSA-44",
                        headers={"kid": self.source.oidc_jwks["keys"][0]["kid"]},
                    ),
                }
            )
        )
        self.assertEqual(profile["sub"], OPENID_USER["sub"])
        self.assertEqual(profile["email"], OPENID_USER["email"])
        self.assertEqual(profile["aud"], client_id)

    @Mocker()
    def test_userinfo_jwt_mldsa_key_unavailable(self, mock: Mocker):
        """An ML-DSA id_token whose key OpenSSL cannot load (ML-DSA under a FIPS provider that
        predates it) fails closed instead of raising"""

        class UnavailablePublicKey:
            @staticmethod
            def from_public_bytes(_data: bytes):
                raise UnsupportedAlgorithm("ML-DSA is not supported by this version of OpenSSL")

        jwks_cert = create_test_cert(PrivateKeyAlg.MLDSA44)
        client_id = generate_id()
        self.source.profile_url = ""
        self.source.consumer_key = client_id
        self.source.oidc_jwks = {"keys": [mldsa_jwk(jwks_cert)]}
        self.source.save()
        now = int(time.time())
        id_token = encode(
            {
                "iss": "https://example.com",
                "sub": OPENID_USER["sub"],
                "aud": client_id,
                "exp": now + 3600,
                "iat": now,
            },
            key=jwks_cert.private_key,
            algorithm="ML-DSA-44",
            headers={"kid": self.source.oidc_jwks["keys"][0]["kid"]},
        )
        with patch.dict(
            "authentik.lib.jwt_mldsa.MLDSA_ALGORITHMS",
            {"ML-DSA-44": (MLDSA44PrivateKey, UnavailablePublicKey)},
        ):
            profile = (
                OpenIDConnectOAuth2Callback(request=self.factory.get("/"))
                .get_client(self.source)
                .get_profile_info(
                    {
                        "token_type": "Bearer",
                        "access_token": generate_id(),
                        "id_token": id_token,
                    }
                )
            )
        self.assertIsNone(profile)
