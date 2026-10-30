"""Test token view"""

from datetime import datetime, timedelta
from json import loads
from unittest.mock import patch

from cryptography.exceptions import UnsupportedAlgorithm
from cryptography.hazmat.primitives.asymmetric.mldsa import MLDSA44PrivateKey
from django.test import RequestFactory
from django.urls import reverse
from jwt import decode, encode

from authentik.blueprints.tests import apply_blueprint
from authentik.common.oauth.constants import (
    GRANT_TYPE_CLIENT_CREDENTIALS,
    SCOPE_OPENID,
    SCOPE_OPENID_EMAIL,
    SCOPE_OPENID_PROFILE,
    TOKEN_TYPE,
)
from authentik.core.models import USERNAME_MAX_LENGTH, Application, Group, User
from authentik.core.tests.utils import create_test_cert, create_test_flow
from authentik.crypto.builder import PrivateKeyAlg
from authentik.crypto.models import CertificateKeyPair
from authentik.lib.generators import generate_id
from authentik.lib.jwt_mldsa import MLDSAAlgorithm
from authentik.policies.models import PolicyBinding
from authentik.providers.oauth2.models import (
    GrantType,
    OAuth2Provider,
    RedirectURI,
    RedirectURIMatchingMode,
    ScopeMapping,
)
from authentik.providers.oauth2.tests.utils import OAuthTestCase
from authentik.providers.oauth2.views.jwks import JWKSView
from authentik.sources.oauth.models import OAuthSource, OAuthSourcePropertyMapping


def mldsa_jwk(cert: CertificateKeyPair) -> dict:
    """Public AKP JWK (RFC 9964) for an ML-DSA certificate, as an upstream IdP would publish it"""
    jwk = MLDSAAlgorithm.to_jwk(cert.private_key.public_key(), as_dict=True)
    jwk["kid"] = cert.kid
    jwk["use"] = "sig"
    return jwk


class TestTokenClientCredentialsJWTSource(OAuthTestCase):
    """Test token (client_credentials, with JWT) view"""

    @apply_blueprint("system/providers-oauth2.yaml")
    def setUp(self) -> None:
        super().setUp()
        self.factory = RequestFactory()
        self.other_cert = create_test_cert()
        # Provider used as a helper to sign JWTs with the same key as the OAuth source has
        self.helper_provider = OAuth2Provider.objects.create(
            name=generate_id(),
            authorization_flow=create_test_flow(),
            signing_key=self.other_cert,
        )
        self.cert = create_test_cert()

        jwk = JWKSView().get_jwk_for_key(self.other_cert, "sig")
        self.source: OAuthSource = OAuthSource.objects.create(
            name=generate_id(),
            slug=generate_id(),
            provider_type="openidconnect",
            consumer_key=generate_id(),
            consumer_secret=generate_id(),
            authorization_url="http://foo",
            access_token_url=f"http://{generate_id()}",
            profile_url="http://foo",
            oidc_well_known_url="",
            oidc_jwks_url="",
            oidc_jwks={
                "keys": [jwk],
            },
        )

        self.provider: OAuth2Provider = OAuth2Provider.objects.create(
            name="test",
            authorization_flow=create_test_flow(),
            redirect_uris=[RedirectURI(RedirectURIMatchingMode.STRICT, "http://testserver")],
            signing_key=self.cert,
            grant_types=[GrantType.CLIENT_CREDENTIALS],
        )
        self.provider.jwt_federation_sources.add(self.source)
        self.provider.property_mappings.set(ScopeMapping.objects.all())
        self.app = Application.objects.create(name="test", slug="test", provider=self.provider)

    def test_invalid_type(self):
        """test invalid type"""
        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            {
                "grant_type": GRANT_TYPE_CLIENT_CREDENTIALS,
                "scope": f"{SCOPE_OPENID} {SCOPE_OPENID_EMAIL} {SCOPE_OPENID_PROFILE}",
                "client_id": self.provider.client_id,
                "client_assertion_type": "foo",
                "client_assertion": "foo.bar",
            },
        )
        self.assertEqual(response.status_code, 400)
        body = loads(response.content.decode())
        self.assertEqual(body["error"], "invalid_grant")

    def test_invalid_jwt(self):
        """test invalid JWT"""
        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            {
                "grant_type": GRANT_TYPE_CLIENT_CREDENTIALS,
                "scope": f"{SCOPE_OPENID} {SCOPE_OPENID_EMAIL} {SCOPE_OPENID_PROFILE}",
                "client_id": self.provider.client_id,
                "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
                "client_assertion": "foo.bar",
            },
        )
        self.assertEqual(response.status_code, 400)
        body = loads(response.content.decode())
        self.assertEqual(body["error"], "invalid_grant")

    def test_invalid_signature(self):
        """test invalid JWT"""
        token = self.helper_provider.encode(
            {
                "sub": "foo",
                "exp": datetime.now() + timedelta(hours=2),
            }
        )
        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            {
                "grant_type": GRANT_TYPE_CLIENT_CREDENTIALS,
                "scope": f"{SCOPE_OPENID} {SCOPE_OPENID_EMAIL} {SCOPE_OPENID_PROFILE}",
                "client_id": self.provider.client_id,
                "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
                "client_assertion": token + "foo",
            },
        )
        self.assertEqual(response.status_code, 400)
        body = loads(response.content.decode())
        self.assertEqual(body["error"], "invalid_grant")

    def test_invalid_expired(self):
        """test invalid JWT"""
        token = self.helper_provider.encode(
            {
                "sub": "foo",
                "exp": datetime.now() - timedelta(hours=2),
            }
        )
        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            {
                "grant_type": GRANT_TYPE_CLIENT_CREDENTIALS,
                "scope": f"{SCOPE_OPENID} {SCOPE_OPENID_EMAIL} {SCOPE_OPENID_PROFILE}",
                "client_id": self.provider.client_id,
                "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
                "client_assertion": token,
            },
        )
        self.assertEqual(response.status_code, 400)
        body = loads(response.content.decode())
        self.assertEqual(body["error"], "invalid_grant")

    def test_invalid_no_app(self):
        """test invalid JWT"""
        self.app.provider = None
        self.app.save()
        token = self.helper_provider.encode(
            {
                "sub": "foo",
                "exp": datetime.now() + timedelta(hours=2),
            }
        )
        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            {
                "grant_type": GRANT_TYPE_CLIENT_CREDENTIALS,
                "scope": f"{SCOPE_OPENID} {SCOPE_OPENID_EMAIL} {SCOPE_OPENID_PROFILE}",
                "client_id": self.provider.client_id,
                "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
                "client_assertion": token,
            },
        )
        self.assertEqual(response.status_code, 400)
        body = loads(response.content.decode())
        self.assertEqual(body["error"], "invalid_grant")

    def test_invalid_access_denied(self):
        """test invalid JWT"""
        group = Group.objects.create(name="foo")
        PolicyBinding.objects.create(
            group=group,
            target=self.app,
            order=0,
        )
        token = self.helper_provider.encode(
            {
                "sub": "foo",
                "exp": datetime.now() + timedelta(hours=2),
            }
        )
        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            {
                "grant_type": GRANT_TYPE_CLIENT_CREDENTIALS,
                "scope": f"{SCOPE_OPENID} {SCOPE_OPENID_EMAIL} {SCOPE_OPENID_PROFILE}",
                "client_id": self.provider.client_id,
                "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
                "client_assertion": token,
            },
        )
        self.assertEqual(response.status_code, 400)
        body = loads(response.content.decode())
        self.assertEqual(body["error"], "invalid_grant")

    def test_successful(self):
        """test successful"""
        token = self.helper_provider.encode(
            {
                "sub": "foo",
                "exp": datetime.now() + timedelta(hours=2),
            }
        )
        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            {
                "grant_type": GRANT_TYPE_CLIENT_CREDENTIALS,
                "scope": f"{SCOPE_OPENID} {SCOPE_OPENID_EMAIL} {SCOPE_OPENID_PROFILE}",
                "client_id": self.provider.client_id,
                "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
                "client_assertion": token,
            },
        )
        self.assertEqual(response.status_code, 200)

        user = User.objects.filter(username=f"{self.provider.name}-foo").first()
        self.assertIsNotNone(user)

        body = loads(response.content.decode())
        self.assertEqual(body["token_type"], TOKEN_TYPE)
        _, alg = self.provider.jwt_key
        jwt = decode(
            body["access_token"],
            key=self.provider.signing_key.public_key,
            algorithms=[alg],
            audience=self.provider.client_id,
        )
        self.assertEqual(
            jwt["given_name"], "Autogenerated user from application test (client credentials JWT)"
        )
        self.assertEqual(jwt["preferred_username"], "test-foo")

    def test_successful_attributes_verifying_source(self):
        """A second federation source advertising the same kid must not be credited with
        the verification. The resolved source selects the user path and property mappings,
        so crediting the wrong one creates the user under the wrong source."""
        real_jwk = JWKSView().get_jwk_for_key(self.other_cert, "sig")
        # Same kid, different key material: this source is found by the kid lookup but
        # can never verify the assertion.
        decoy_jwk = JWKSView().get_jwk_for_key(create_test_cert(), "sig")
        decoy_jwk["kid"] = real_jwk["kid"]
        decoy_source = OAuthSource.objects.create(
            name=generate_id(),
            slug=generate_id(),
            provider_type="openidconnect",
            consumer_key=generate_id(),
            consumer_secret=generate_id(),
            authorization_url="http://foo",
            access_token_url=f"http://{generate_id()}",
            profile_url="http://foo",
            oidc_well_known_url="",
            oidc_jwks_url="",
            oidc_jwks={"keys": [decoy_jwk]},
        )
        self.provider.jwt_federation_sources.add(decoy_source)

        token = self.helper_provider.encode(
            {
                "sub": "foo",
                "exp": datetime.now() + timedelta(hours=2),
            }
        )
        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            {
                "grant_type": GRANT_TYPE_CLIENT_CREDENTIALS,
                "scope": f"{SCOPE_OPENID} {SCOPE_OPENID_EMAIL} {SCOPE_OPENID_PROFILE}",
                "client_id": self.provider.client_id,
                "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
                "client_assertion": token,
            },
        )
        self.assertEqual(response.status_code, 200)

        user = User.objects.filter(username=f"{self.provider.name}-foo").first()
        self.assertIsNotNone(user)
        self.assertEqual(user.path, self.source.get_user_path())
        self.assertNotEqual(user.path, decoy_source.get_user_path())

    def test_successful_mapping(self):
        """test successful"""
        test_username = ("mapped-foo" + ("a" * 150))[:USERNAME_MAX_LENGTH]
        mapping = OAuthSourcePropertyMapping.objects.create(
            name="test-mapping",
            expression="""return {
                "email": oauth_userinfo.get("email"),
                "name": oauth_userinfo.get("name"),
                "username": oauth_userinfo.get("username"),
            }""",
        )
        self.source.user_property_mappings.add(mapping)

        token = self.helper_provider.encode(
            {
                "sub": "foo",
                "email": "test-user@example.com",
                "name": "Mapped Test User",
                "username": "mapped-foo" + ("a" * 150),
                "exp": datetime.now() + timedelta(hours=2),
            }
        )
        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            {
                "grant_type": GRANT_TYPE_CLIENT_CREDENTIALS,
                "scope": f"{SCOPE_OPENID} {SCOPE_OPENID_EMAIL} {SCOPE_OPENID_PROFILE}",
                "client_id": self.provider.client_id,
                "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
                "client_assertion": token,
            },
        )
        self.assertEqual(response.status_code, 200)

        user = User.objects.filter(username=test_username).first()
        self.assertIsNotNone(user)

        body = loads(response.content.decode())
        self.assertEqual(body["token_type"], TOKEN_TYPE)
        key_obj, alg = self.provider.jwt_key
        jwt = decode(
            body["access_token"],
            key=key_obj.public_key(),
            algorithms=[alg],
            audience=self.provider.client_id,
        )

        self.assertEqual(jwt["email"], "test-user@example.com")
        self.assertEqual(jwt["given_name"], "Mapped Test User")
        self.assertEqual(jwt["preferred_username"], test_username)

    def test_successful_mldsa_source(self):
        """test successful with a client assertion signed by an ML-DSA key (RFC 9964 AKP JWK)"""
        mldsa_cert = create_test_cert(PrivateKeyAlg.MLDSA44)
        jwk = mldsa_jwk(mldsa_cert)
        self.assertEqual(jwk["kty"], "AKP")
        self.assertEqual(jwk["alg"], "ML-DSA-44")
        self.source.oidc_jwks = {"keys": [jwk]}
        self.source.save()
        token = encode(
            {
                "sub": "foo",
                "exp": datetime.now() + timedelta(hours=2),
            },
            key=mldsa_cert.private_key,
            algorithm="ML-DSA-44",
            headers={"kid": mldsa_cert.kid},
        )
        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            {
                "grant_type": GRANT_TYPE_CLIENT_CREDENTIALS,
                "scope": f"{SCOPE_OPENID} {SCOPE_OPENID_EMAIL} {SCOPE_OPENID_PROFILE}",
                "client_id": self.provider.client_id,
                "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
                "client_assertion": token,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(User.objects.filter(username=f"{self.provider.name}-foo").first())

    def test_successful_mldsa_key_unavailable(self):
        """An AKP key in the source's JWKS that OpenSSL cannot load (ML-DSA under a FIPS provider
        that predates it) is skipped, and the remaining keys are still tried"""

        class UnavailablePublicKey:
            @staticmethod
            def from_public_bytes(_data: bytes):
                raise UnsupportedAlgorithm("ML-DSA is not supported by this version of OpenSSL")

        mldsa_cert = create_test_cert(PrivateKeyAlg.MLDSA44)
        unavailable_jwk = mldsa_jwk(mldsa_cert)
        # Without a kid, the key is not skipped by the kid match and must actually be loaded
        del unavailable_jwk["kid"]
        helper_jwk = JWKSView().get_jwk_for_key(self.other_cert, "sig")
        self.source.oidc_jwks = {"keys": [unavailable_jwk, helper_jwk]}
        self.source.save()
        token = self.helper_provider.encode(
            {
                "sub": "foo",
                "exp": datetime.now() + timedelta(hours=2),
            }
        )
        with patch.dict(
            "authentik.lib.jwt_mldsa.MLDSA_ALGORITHMS",
            {"ML-DSA-44": (MLDSA44PrivateKey, UnavailablePublicKey)},
        ):
            response = self.client.post(
                reverse("authentik_providers_oauth2:token"),
                {
                    "grant_type": GRANT_TYPE_CLIENT_CREDENTIALS,
                    "scope": f"{SCOPE_OPENID} {SCOPE_OPENID_EMAIL} {SCOPE_OPENID_PROFILE}",
                    "client_id": self.provider.client_id,
                    "client_assertion_type": (
                        "urn:ietf:params:oauth:client-assertion-type:jwt-bearer"
                    ),
                    "client_assertion": token,
                },
            )
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(User.objects.filter(username=f"{self.provider.name}-foo").first())
