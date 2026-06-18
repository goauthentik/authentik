"""Security regression tests for JWT algorithm-confusion attacks against the
client_credentials JWT-bearer grant.

These cover the negative path where an attacker crafts a JWT whose ``alg`` header
does not match the algorithm the configured source JWK is meant to be verified
with. References: RFC 9700 §4.5 (algorithm confusion), the "alg:none" signature
bypass class (CVE-2015-9235 and relatives), and the asymmetric/HMAC key-confusion
pattern (using a published RSA public key as an HMAC secret).

The verification path under test is
``TokenParams._TokenParams__validate_jwt_from_source`` in
``authentik/providers/oauth2/views/token.py``. Note that when a source JWK omits
the optional ``alg`` member, verification falls back to the (attacker controlled)
algorithm from the JWT header -- exactly the precondition for a confusion attack.
These tests assert the forgeries are rejected regardless.
"""

import hashlib
import hmac
from base64 import urlsafe_b64encode
from copy import deepcopy
from datetime import datetime, timedelta
from json import dumps, loads

from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from django.test import RequestFactory
from django.urls import reverse
from jwt import encode

from authentik.blueprints.tests import apply_blueprint
from authentik.common.oauth.constants import (
    CLIENT_ASSERTION_TYPE_JWT,
    GRANT_TYPE_CLIENT_CREDENTIALS,
    SCOPE_OPENID,
    SCOPE_OPENID_EMAIL,
    SCOPE_OPENID_PROFILE,
)
from authentik.core.models import Application, User
from authentik.core.tests.utils import create_test_cert, create_test_flow
from authentik.lib.generators import generate_id
from authentik.providers.oauth2.models import (
    GrantType,
    OAuth2Provider,
    RedirectURI,
    RedirectURIMatchingMode,
    ScopeMapping,
)
from authentik.providers.oauth2.tests.utils import OAuthTestCase
from authentik.providers.oauth2.views.jwks import JWKSView
from authentik.sources.oauth.models import OAuthSource


class TestTokenJWTAlgConfusion(OAuthTestCase):
    """Algorithm-confusion negative-path tests for the JWT-bearer grant."""

    @apply_blueprint("system/providers-oauth2.yaml")
    def setUp(self) -> None:
        super().setUp()
        self.factory = RequestFactory()
        # Cert whose public key backs the trusted source JWK -- an attacker can
        # read this public key from the source's JWKS endpoint.
        self.source_cert = create_test_cert()
        self.provider_cert = create_test_cert()

        jwk = JWKSView().get_jwk_for_key(self.source_cert, "sig")
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
            oidc_jwks={"keys": [jwk]},
        )

        self.provider: OAuth2Provider = OAuth2Provider.objects.create(
            name=generate_id(),
            authorization_flow=create_test_flow(),
            redirect_uris=[RedirectURI(RedirectURIMatchingMode.STRICT, "http://testserver")],
            signing_key=self.provider_cert,
            grant_types=[GrantType.CLIENT_CREDENTIALS],
        )
        self.provider.jwt_federation_sources.add(self.source)
        self.provider.property_mappings.set(ScopeMapping.objects.all())
        self.app = Application.objects.create(
            name=generate_id(), slug=generate_id(), provider=self.provider
        )

    def _public_key_secret_candidates(self) -> dict[str, bytes]:
        """The public-key byte representations a real attacker would scrape from
        the published JWKS/cert and try as the forged HMAC secret. These are the
        two representations actual tooling (e.g. jwt_tool) uses for HS/RS
        confusion: the bare public key PEM and the x5c certificate PEM."""
        public_key = self.source_cert.public_key
        return {
            "spki_pem": public_key.public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo),
            "cert_pem": self.source_cert.certificate.public_bytes(Encoding.PEM),
        }

    @staticmethod
    def _forge_hs256(payload: dict, secret: bytes, kid: str) -> str:
        """Hand-craft an HS256-signed JWT. PyJWT's ``encode`` refuses to use an
        asymmetric key as an HMAC secret, so -- like jwt_tool and other offensive
        tooling -- we build the token manually to faithfully simulate the attack."""

        def segment(data: bytes) -> bytes:
            return urlsafe_b64encode(data).rstrip(b"=")

        header = segment(dumps({"alg": "HS256", "typ": "JWT", "kid": kid}).encode())
        body = segment(dumps(payload).encode())
        signing_input = header + b"." + body
        signature = segment(hmac.new(secret, signing_input, hashlib.sha256).digest())
        return (signing_input + b"." + signature).decode()

    @staticmethod
    def _exp() -> int:
        return int((datetime.now() + timedelta(hours=2)).timestamp())

    def _post_assertion(self, assertion: str):
        return self.client.post(
            reverse("authentik_providers_oauth2:token"),
            {
                "grant_type": GRANT_TYPE_CLIENT_CREDENTIALS,
                "scope": f"{SCOPE_OPENID} {SCOPE_OPENID_EMAIL} {SCOPE_OPENID_PROFILE}",
                "client_id": self.provider.client_id,
                "client_assertion_type": CLIENT_ASSERTION_TYPE_JWT,
                "client_assertion": assertion,
            },
        )

    def _assert_rejected(self, response):
        self.assertEqual(response.status_code, 400)
        self.assertEqual(loads(response.content.decode())["error"], "invalid_grant")
        # A rejected assertion must not auto-provision a user as a side effect
        self.assertIsNone(User.objects.filter(username=f"{self.provider.name}-foo").first())

    def test_alg_none(self):
        """An unsigned (alg:none) assertion with a valid kid must be rejected."""
        forged = encode(
            {"sub": "foo", "exp": self._exp()},
            key="",
            algorithm="none",
            headers={"kid": self.source_cert.kid},
        )
        self._assert_rejected(self._post_assertion(forged))

    def test_hs256_confusion_with_alg_in_jwk(self):
        """HS256 forgery signed with the source's RSA public key, against a JWK
        that pins alg=RS256. The header-declared HS256 must not be honored, for
        any public-key byte representation the attacker might use as the secret."""
        for label, secret in self._public_key_secret_candidates().items():
            with self.subTest(secret=label):
                forged = self._forge_hs256(
                    {"sub": "foo", "exp": self._exp()},
                    secret=secret,
                    kid=self.source_cert.kid,
                )
                self._assert_rejected(self._post_assertion(forged))

    def test_hs256_confusion_without_alg_in_jwk(self):
        """The dangerous case: when the source JWK omits ``alg``, verification
        falls back to the attacker-controlled header algorithm. An HS256 forgery
        signed with the RSA public key must still be rejected (PyJWT refuses to
        use an asymmetric key as an HMAC secret) -- for every public-key byte
        representation the attacker might try as the secret."""
        # Rebuild the source's JWK set without the alg member to force the fallback
        jwks = deepcopy(self.source.oidc_jwks)
        for key in jwks["keys"]:
            key.pop("alg", None)
        self.source.oidc_jwks = jwks
        self.source.save()

        for label, secret in self._public_key_secret_candidates().items():
            with self.subTest(secret=label):
                forged = self._forge_hs256(
                    {"sub": "foo", "exp": self._exp()},
                    secret=secret,
                    kid=self.source_cert.kid,
                )
                self._assert_rejected(self._post_assertion(forged))

    def test_kid_swapped_to_unrelated_key(self):
        """A token signed with an unrelated key but carrying a kid that matches a
        trusted source JWK must not verify."""
        forged = encode(
            {"sub": "foo", "exp": self._exp()},
            key=self.provider_cert.private_key,  # not the source's key
            algorithm="RS256",
            headers={"kid": self.source_cert.kid},
        )
        self._assert_rejected(self._post_assertion(forged))
