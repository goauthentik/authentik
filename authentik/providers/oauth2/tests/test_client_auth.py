"""Test private_key_jwt client authentication"""

import hashlib
import hmac
import json
import time
from base64 import b64encode, urlsafe_b64encode
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from threading import Barrier
from typing import Any
from unittest.mock import patch

from cryptography.hazmat.primitives.asymmetric.ec import SECP256R1, SECP384R1
from cryptography.hazmat.primitives.asymmetric.ec import generate_private_key as generate_ec
from cryptography.hazmat.primitives.asymmetric.rsa import generate_private_key as generate_rsa
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from django.core.cache import caches
from django.db import DatabaseError, connection
from django.test import RequestFactory, TestCase, TransactionTestCase
from jwt import encode
from jwt.algorithms import ECAlgorithm, RSAAlgorithm

from authentik.common.oauth.constants import (
    CLIENT_ASSERTION,
    CLIENT_ASSERTION_TYPE,
    CLIENT_ASSERTION_TYPE_JWT,
)
from authentik.core.tests.utils import create_test_cert, create_test_flow
from authentik.lib.generators import generate_id
from authentik.providers.oauth2.client import OAuthClientContext, OAuthClientResolver
from authentik.providers.oauth2.client_auth import (
    ClientAssertionPolicy,
    ClientAssertionVerifier,
    ClientAuthenticationError,
    ClientAuthMethod,
    ClientKeysUnavailable,
    InvalidClientKey,
    PresentedClientCredentials,
    StaticClientKeySource,
    TrustedClientKey,
    authenticate_private_key_jwt,
    parse_client_credentials,
    parse_jwks,
)
from authentik.providers.oauth2.models import ClientType, OAuth2Provider

CLIENT_ID = "https://agent.example/client.json"
ISSUER = "https://authentik.example/application/o/app/"
TOKEN_ENDPOINT = "https://authentik.example/application/o/token/"
POLICY = ClientAssertionPolicy(audiences=frozenset({ISSUER, TOKEN_ENDPOINT}))


@dataclass
class SigningKey:
    """A client's key pair, published as a JWK"""

    private: Any
    alg: str
    kid: str | None = field(default_factory=generate_id)

    @staticmethod
    def ec(alg="ES256", curve=None, kid: str | None = "") -> SigningKey:
        key = SigningKey(generate_ec(curve or SECP256R1()), alg)
        if kid != "":
            key.kid = kid
        return key

    @staticmethod
    def rsa(alg="RS256", size=2048) -> SigningKey:
        return SigningKey(generate_rsa(public_exponent=65537, key_size=size), alg)

    def jwk(self, **extra) -> dict[str, Any]:
        algorithm = ECAlgorithm if self.alg.startswith("ES") else RSAAlgorithm
        jwk = algorithm.to_jwk(self.private.public_key(), as_dict=True)
        if self.kid is not None:
            jwk["kid"] = self.kid
        jwk.update(extra)
        return jwk

    def trusted(self) -> TrustedClientKey:
        return TrustedClientKey.from_jwk(self.jwk())

    def sign(self, claims: dict[str, Any] | None = None, headers=None, alg=None, **overrides):
        now = int(time.time())
        payload = {
            "iss": CLIENT_ID,
            "sub": CLIENT_ID,
            "aud": TOKEN_ENDPOINT,
            "iat": now,
            "exp": now + 60,
            "jti": generate_id(),
        }
        payload.update(claims or {})
        for name, value in overrides.items():
            if value is None:
                payload.pop(name, None)
            else:
                payload[name] = value
        header = {"kid": self.kid} if self.kid is not None else {}
        header.update(headers or {})
        return encode(payload, self.private, algorithm=alg or self.alg, headers=header)


class RotatingKeySource:
    """Key source standing in for a cached remote JWKS: serves `current` until refreshed,
    then `next`. Counts how often refresh was requested."""

    def __init__(self, current: list[TrustedClientKey], next_keys: list[TrustedClientKey]):
        self.current = current
        self.next = next_keys
        self.refreshes = 0

    def get_keys(self, *, refresh: bool = False):
        if refresh:
            self.refreshes += 1
            self.current = self.next
        return self.current


class TestClientAssertionVerifier(TestCase):
    """Verify client assertions against injected keys"""

    def setUp(self):
        self.key = SigningKey.ec()
        self.verifier = ClientAssertionVerifier(
            StaticClientKeySource((self.key.trusted(),)), POLICY
        )

    def assertRejected(self, assertion: str, cause: str, verifier=None, client_id=CLIENT_ID):
        with self.assertRaises(ClientAuthenticationError) as ctx:
            (verifier or self.verifier).verify(assertion, client_id)
        self.assertEqual(ctx.exception.cause, cause)
        self.assertEqual(ctx.exception.error, "invalid_client")

    def test_valid(self):
        for key in (
            SigningKey.ec(),
            SigningKey.ec("ES384", SECP384R1()),
            SigningKey.rsa(),
            SigningKey.rsa("PS256"),
        ):
            with self.subTest(alg=key.alg):
                verifier = ClientAssertionVerifier(StaticClientKeySource((key.trusted(),)), POLICY)
                verified = verifier.verify(key.sign(), CLIENT_ID)
                self.assertEqual(verified.client_id, CLIENT_ID)
                self.assertEqual(verified.algorithm, key.alg)
                self.assertEqual(verified.key_id, key.kid)
                self.assertEqual(verified.key_thumbprint, key.trusted().thumbprint)
                self.assertEqual(verified.audience, TOKEN_ENDPOINT)

    def test_audience_aliases(self):
        self.verifier.verify(self.key.sign(aud=ISSUER), CLIENT_ID)
        self.verifier.verify(self.key.sign(aud=[ISSUER]), CLIENT_ID)
        self.assertRejected(self.key.sign(aud="https://other.example/token"), "invalid_audience")
        # The configured aliases are matched exactly
        self.assertRejected(self.key.sign(aud=TOKEN_ENDPOINT.rstrip("/")), "invalid_audience")
        self.assertRejected(self.key.sign(aud=TOKEN_ENDPOINT.upper()), "invalid_audience")
        # Local policy: a single audience value only
        self.assertRejected(self.key.sign(aud=[ISSUER, TOKEN_ENDPOINT]), "invalid_audience")
        self.assertRejected(self.key.sign(aud=[]), "invalid_audience")
        self.assertRejected(self.key.sign(aud=None), "invalid_claims")

    def test_issuer_subject(self):
        self.assertRejected(
            self.key.sign(iss="https://other.example/client.json"), "invalid_issuer"
        )
        self.assertRejected(
            self.key.sign(sub="https://other.example/client.json"), "invalid_subject"
        )
        # A JWT bearer grant assertion: issued by the client, about a user
        self.assertRejected(self.key.sign(sub="user@example.com"), "invalid_subject")
        self.assertRejected(self.key.sign(iss=None), "invalid_claims")
        self.assertRejected(self.key.sign(sub=None), "invalid_claims")
        # Verified for a different client than the one that signed it
        self.assertRejected(self.key.sign(), "invalid_issuer", client_id="other-client")

    def test_time_bounds(self):
        now = int(time.time())
        self.assertRejected(self.key.sign(exp=now - 120, iat=now - 180), "expired")
        self.assertRejected(self.key.sign(exp=None), "invalid_claims")
        self.assertRejected(self.key.sign(iat=None), "invalid_claims")
        self.assertRejected(self.key.sign(iat=now + 120, exp=now + 180), "not_yet_valid")
        self.assertRejected(self.key.sign(nbf=now + 120), "not_yet_valid")
        self.assertRejected(self.key.sign(iat=now - 600, exp=now + 60), "too_old")
        self.assertRejected(self.key.sign(exp=now + 7200), "lifetime_exceeded")
        self.assertRejected(self.key.sign(exp=now, iat=now + 10), "lifetime_exceeded")
        self.assertRejected(self.key.sign(iat=True), "invalid_claim")
        self.assertRejected(self.key.sign(iat="now"), "invalid_claims")
        # Within leeway is accepted
        self.verifier.verify(self.key.sign(exp=now - 10, iat=now - 70), CLIENT_ID)
        self.verifier.verify(self.key.sign(iat=now + 10, exp=now + 70), CLIENT_ID)

    def test_jti(self):
        self.assertRejected(self.key.sign(jti=None), "invalid_claims")
        self.assertRejected(self.key.sign(jti=""), "invalid_claim")
        self.assertRejected(self.key.sign(jti=123), "invalid_claims")
        self.assertRejected(self.key.sign(jti="a" * 257), "invalid_claim")

    def test_replay(self):
        assertion = self.key.sign()
        self.verifier.verify(assertion, CLIENT_ID)
        self.assertRejected(assertion, "replayed")
        # A different assertion re-using the jti is also a replay
        jti = generate_id()
        self.verifier.verify(self.key.sign(jti=jti), CLIENT_ID)
        self.assertRejected(self.key.sign(jti=jti, aud=ISSUER), "replayed")

    def test_replay_scope(self):
        """jti is unique per issuer: other clients may use the same value"""
        jti = generate_id()
        other = SigningKey.ec()
        other_verifier = ClientAssertionVerifier(StaticClientKeySource((other.trusted(),)), POLICY)
        self.verifier.verify(self.key.sign(jti=jti), CLIENT_ID)
        other_verifier.verify(
            other.sign(jti=jti, iss="other-client", sub="other-client"), "other-client"
        )

    def test_replay_record(self):
        """Only a hash is stored, and it expires after the acceptance window"""
        jti = generate_id()
        assertion = self.key.sign(jti=jti)
        cache = caches["default"]
        with patch.object(cache, "add", wraps=cache.add) as add:
            self.verifier.verify(assertion, CLIENT_ID)
        key, value = add.call_args.args
        timeout = add.call_args.kwargs["timeout"]
        self.assertNotIn(jti, key)
        self.assertNotIn(CLIENT_ID, key)
        self.assertIs(value, True)
        # min(exp + leeway, iat + max_age) - now, plus margin
        self.assertGreaterEqual(timeout, 90)
        self.assertLessEqual(timeout, 97)

    def test_replay_cache_failure(self):
        """A failing cache fails closed"""
        with patch.object(caches["default"], "_cursor", side_effect=DatabaseError):
            self.assertRejected(self.key.sign(), "replayed")
        with patch.object(caches["default"], "add", side_effect=DatabaseError):
            self.assertRejected(self.key.sign(), "replay_check_failed")

    def test_replay_not_recorded_for_invalid(self):
        """Rejected assertions don't consume their jti"""
        jti = generate_id()
        self.assertRejected(self.key.sign(jti=jti, aud="https://other.example"), "invalid_audience")
        self.verifier.verify(self.key.sign(jti=jti), CLIENT_ID)

    def test_wrong_key(self):
        attacker = SigningKey.ec(kid=self.key.kid)
        self.assertRejected(attacker.sign(), "invalid_signature")
        self.assertRejected(SigningKey.ec().sign(), "unknown_key")

    def test_unsupported_algorithms(self):
        assertion = encode(
            {"iss": CLIENT_ID, "sub": CLIENT_ID, "aud": TOKEN_ENDPOINT, "jti": generate_id()},
            "secret",
            algorithm="HS256",
            headers={"kid": self.key.kid},
        )
        self.assertRejected(assertion, "unsupported_algorithm")
        unsecured = encode({"iss": CLIENT_ID}, None, algorithm="none")
        self.assertRejected(unsecured, "unsupported_algorithm")
        # Policy restricts to RSA only
        rsa_only = ClientAssertionVerifier(
            StaticClientKeySource((self.key.trusted(),)),
            ClientAssertionPolicy(audiences=POLICY.audiences, algorithms=frozenset({"RS256"})),
        )
        self.assertRejected(self.key.sign(), "unsupported_algorithm", verifier=rsa_only)

    def test_algorithm_confusion(self):
        """An HMAC signature keyed with the client's public key is never accepted"""
        rsa = SigningKey.rsa()
        verifier = ClientAssertionVerifier(StaticClientKeySource((rsa.trusted(),)), POLICY)
        pem = rsa.private.public_key().public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo)
        now = int(time.time())
        claims = {
            "iss": CLIENT_ID,
            "sub": CLIENT_ID,
            "aud": TOKEN_ENDPOINT,
            "iat": now,
            "exp": now + 60,
            "jti": generate_id(),
        }

        def b64(data: bytes) -> str:
            return urlsafe_b64encode(data).rstrip(b"=").decode()

        for alg in ("HS256", "HS512"):
            signing_input = (
                f"{b64(json.dumps({'alg': alg, 'kid': rsa.kid}).encode())}."
                f"{b64(json.dumps(claims).encode())}"
            )
            digest = hashlib.sha256 if alg == "HS256" else hashlib.sha512
            sig = hmac.new(pem, signing_input.encode(), digest).digest()
            self.assertRejected(f"{signing_input}.{b64(sig)}", "unsupported_algorithm", verifier)
        # An EC key cannot verify an RSA algorithm and vice versa
        self.assertRejected(rsa.sign(headers={"kid": self.key.kid}), "key_algorithm_mismatch")
        # A key pinned to an algorithm is not used for another
        pinned = TrustedClientKey.from_jwk(rsa.jwk(alg="PS256"))
        verifier = ClientAssertionVerifier(StaticClientKeySource((pinned,)), POLICY)
        self.assertRejected(rsa.sign(), "key_algorithm_mismatch", verifier)

    def test_untrusted_key_locations(self):
        attacker = SigningKey.ec()
        for name, value in (
            ("jku", "https://attacker.example/jwks.json"),
            ("x5u", "https://attacker.example/cert.pem"),
            ("jwk", attacker.jwk()),
            ("x5c", ["MIIB"]),
        ):
            with self.subTest(header=name):
                # Even when signed with the trusted key
                self.assertRejected(self.key.sign(headers={name: value}), "untrusted_key_location")
                self.assertRejected(attacker.sign(headers={name: value}), "untrusted_key_location")

    def test_headers(self):
        # PyJWT itself rejects unsupported critical headers while parsing
        self.assertRejected(self.key.sign(headers={"crit": ["exp"]}), "malformed_assertion")
        # Header is checked before the signature, so swapping it in is enough here
        _, payload, sig = self.key.sign().split(".")
        bad_kid = urlsafe_b64encode(json.dumps({"alg": "ES256", "kid": 1}).encode()).rstrip(b"=")
        self.assertRejected(f"{bad_kid.decode()}.{payload}.{sig}", "malformed_assertion")
        self.assertRejected(self.key.sign(headers={"kid": ""}), "malformed_assertion")
        for typ in ("JWT", "jwt", "client-authentication+jwt", "application/JWT"):
            with self.subTest(typ=typ):
                self.verifier.verify(self.key.sign(headers={"typ": typ}), CLIENT_ID)

    def test_cross_purpose(self):
        """JWTs made for other purposes, signed by the client's own key, are rejected"""
        for typ in ("at+jwt", "dpop+jwt", "secevent+jwt", "logout+jwt", "token-introspection+jwt"):
            with self.subTest(typ=typ):
                self.assertRejected(self.key.sign(headers={"typ": typ}), "invalid_type")
        # A DPoP proof made with the same key
        now = int(time.time())
        dpop = encode(
            {"htm": "POST", "htu": TOKEN_ENDPOINT, "iat": now, "jti": generate_id()},
            self.key.private,
            algorithm="ES256",
            headers={"typ": "dpop+jwt", "jwk": self.key.jwk()},
        )
        self.assertRejected(dpop, "untrusted_key_location")
        # An assertion this client made for another authorization server
        self.assertRejected(self.key.sign(aud="https://other-as.example/token"), "invalid_audience")
        # An ID token issued by authentik to this client, signed by authentik's key
        cert = create_test_cert()
        id_token = encode(
            {
                "iss": ISSUER,
                "sub": generate_id(),
                "aud": CLIENT_ID,
                "iat": now,
                "exp": now + 60,
                "jti": generate_id(),
            },
            cert.private_key,
            algorithm="RS256",
            headers={"kid": cert.kid},
        )
        self.assertRejected(id_token, "unknown_key")

    def test_malformed(self):
        for assertion in ("", "abc", "a.b", "a.b.c", "a.b.c.d.e", "x" * 9000):
            with self.subTest(assertion=assertion[:10]):
                self.assertRejected(assertion, "malformed_assertion")

    def test_key_selection_without_kid(self):
        single = SigningKey.ec(kid=None)
        verifier = ClientAssertionVerifier(StaticClientKeySource((single.trusted(),)), POLICY)
        verifier.verify(single.sign(), CLIENT_ID)
        # With several keys, a kid is required, even when only one would verify
        other = SigningKey.rsa()
        verifier = ClientAssertionVerifier(
            StaticClientKeySource((single.trusted(), other.trusted())), POLICY
        )
        self.assertRejected(single.sign(), "ambiguous_key", verifier)

    def test_duplicate_kid(self):
        duplicate = SigningKey.ec(kid=self.key.kid)
        verifier = ClientAssertionVerifier(
            StaticClientKeySource((self.key.trusted(), duplicate.trusted())), POLICY
        )
        self.assertRejected(self.key.sign(), "ambiguous_key", verifier)
        with self.assertRaises(InvalidClientKey):
            parse_jwks({"keys": [self.key.jwk(), duplicate.jwk()]})

    def test_rotation(self):
        """An unknown kid refreshes the key source once"""
        new = SigningKey.ec()
        source = RotatingKeySource([self.key.trusted()], [new.trusted()])
        verifier = ClientAssertionVerifier(source, POLICY)
        verifier.verify(self.key.sign(), CLIENT_ID)
        self.assertEqual(source.refreshes, 0)
        verifier.verify(new.sign(), CLIENT_ID)
        self.assertEqual(source.refreshes, 1)
        # The old key has been rotated out
        self.assertRejected(self.key.sign(), "unknown_key", verifier)
        self.assertEqual(source.refreshes, 2)

    def test_refresh_bounded(self):
        """Unknown kids refresh at most once per verification; a known kid with a bad
        signature never refreshes"""
        source = RotatingKeySource([self.key.trusted()], [self.key.trusted()])
        verifier = ClientAssertionVerifier(source, POLICY)
        self.assertRejected(SigningKey.ec().sign(), "unknown_key", verifier)
        self.assertEqual(source.refreshes, 1)
        self.assertRejected(SigningKey.ec(kid=self.key.kid).sign(), "invalid_signature", verifier)
        self.assertEqual(source.refreshes, 1)

    def test_keys_unavailable(self):
        class Unavailable:
            def get_keys(self, *, refresh=False):
                raise ClientKeysUnavailable()

        verifier = ClientAssertionVerifier(Unavailable(), POLICY)
        self.assertRejected(self.key.sign(), "keys_unavailable", verifier)

    def test_no_secrets_logged(self):
        assertion = self.key.sign(aud="https://other.example")
        with patch("authentik.providers.oauth2.client_auth.LOGGER") as logger:
            self.assertRejected(assertion, "invalid_audience")
        logged = repr(logger.mock_calls)
        self.assertNotIn(assertion, logged)
        self.assertNotIn(assertion.split(".")[2], logged)
        self.assertIn("invalid_audience", logged)


class TestTrustedClientKey(TestCase):
    """Validate locally trusted client keys"""

    def test_private_and_symmetric(self):
        key = SigningKey.ec()
        private = ECAlgorithm.to_jwk(key.private, as_dict=True)
        with self.assertRaises(InvalidClientKey):
            TrustedClientKey.from_jwk(private)
        with self.assertRaises(InvalidClientKey):
            TrustedClientKey.from_jwk({"kty": "oct", "k": "c2VjcmV0"})
        with self.assertRaises(InvalidClientKey):
            parse_jwks({"keys": [key.jwk(), private]})
        with self.assertRaises(InvalidClientKey):
            parse_jwks({"keys": [key.jwk(), {"kty": "oct", "k": "c2VjcmV0", "kid": "s"}]})

    def test_unusable(self):
        key = SigningKey.ec()
        for jwk in (
            key.jwk(use="enc"),
            key.jwk(key_ops=["encrypt"]),
            key.jwk(alg="RS256"),
            key.jwk(alg="ES384"),
            key.jwk(alg="HS256"),
            key.jwk(crv="secp256k1"),
            SigningKey.rsa(size=1024).jwk(),
            {"kty": "OKP", "crv": "Ed25519", "x": "11qYAYKxCrfVS_7TyWQHOg7hcvPapiMlrwIaaPcHURo"},
            # ML-DSA keys are accepted for DPoP, not for client authentication
            {"kty": "AKP", "alg": "ML-DSA-44", "pub": "AAAA"},
        ):
            with self.subTest(jwk=jwk):
                with self.assertRaises(InvalidClientKey):
                    TrustedClientKey.from_jwk(jwk)

    def test_strips_extra_members(self):
        key = SigningKey.rsa()
        trusted = TrustedClientKey.from_jwk(
            key.jwk(x5u="https://attacker.example/cert.pem", x5c=["MIIB"], alg="RS256")
        )
        self.assertEqual(set(trusted.public_jwk), {"kty", "n", "e"})
        self.assertEqual(trusted.alg, "RS256")
        # Extra members don't change the key's identity
        self.assertEqual(trusted.thumbprint, TrustedClientKey.from_jwk(key.jwk()).thumbprint)

    def test_parse_jwks_skips_unusable(self):
        sig, enc = SigningKey.ec(), SigningKey.ec()
        keys = parse_jwks({"keys": [sig.jwk(), enc.jwk(use="enc")]})
        self.assertEqual([k.kid for k in keys], [sig.kid])
        verifier = ClientAssertionVerifier(StaticClientKeySource(keys), POLICY)
        with self.assertRaises(ClientAuthenticationError) as ctx:
            verifier.verify(enc.sign(), CLIENT_ID)
        self.assertEqual(ctx.exception.cause, "unknown_key")
        with self.assertRaises(InvalidClientKey):
            parse_jwks({"keys": "nope"})

    def test_policy(self):
        with self.assertRaises(ValueError):
            ClientAssertionPolicy(audiences=frozenset())
        with self.assertRaises(ValueError):
            ClientAssertionPolicy(audiences=frozenset({""}))
        for algs in ({"HS256"}, {"none"}, set()):
            with self.subTest(algs=algs):
                with self.assertRaises(ValueError):
                    ClientAssertionPolicy(audiences=POLICY.audiences, algorithms=frozenset(algs))
        with self.assertRaises(ValueError):
            ClientAssertionPolicy(audiences=POLICY.audiences, max_age=7200, max_lifetime=3600)


class TestParseClientCredentials(TestCase):
    """Parse presented client credentials strictly"""

    def setUp(self):
        self.factory = RequestFactory()
        self.assertion = SigningKey.ec().sign()

    def parse(self, data: dict, basic: tuple[str, str] | None = None, query: str = ""):
        headers = {}
        if basic:
            headers["HTTP_AUTHORIZATION"] = (
                "Basic " + b64encode(f"{basic[0]}:{basic[1]}".encode()).decode()
            )
        return parse_client_credentials(self.factory.post(f"/token{query}", data=data, **headers))

    def assertRejected(self, cause: str, error: str = "invalid_client", **kwargs):
        with self.assertRaises(ClientAuthenticationError) as ctx:
            self.parse(**kwargs)
        self.assertEqual((ctx.exception.cause, ctx.exception.error), (cause, error))

    def jwt_data(self, **extra):
        return {
            CLIENT_ASSERTION_TYPE: CLIENT_ASSERTION_TYPE_JWT,
            CLIENT_ASSERTION: self.assertion,
            **extra,
        }

    def test_methods(self):
        creds = self.parse(self.jwt_data())
        self.assertEqual(creds.method, ClientAuthMethod.PRIVATE_KEY_JWT)
        self.assertEqual(creds.client_id, CLIENT_ID)
        self.assertNotIn(self.assertion, repr(creds))
        creds = self.parse(self.jwt_data(client_id=CLIENT_ID))
        self.assertEqual(creds.client_id, CLIENT_ID)
        creds = self.parse({}, basic=("id", "s3cr3t-value"))
        self.assertEqual(
            (creds.method, creds.client_id), (ClientAuthMethod.CLIENT_SECRET_BASIC, "id")
        )
        self.assertNotIn("s3cr3t-value", repr(creds))
        creds = self.parse({"client_id": "id", "client_secret": "secret"})
        self.assertEqual(creds.method, ClientAuthMethod.CLIENT_SECRET_POST)
        creds = self.parse({"client_id": "id", "client_secret": ""})
        self.assertEqual(creds.method, ClientAuthMethod.NONE)

    def test_conflicts(self):
        self.assertRejected(
            "multiple_auth_methods", "invalid_request", data=self.jwt_data(), basic=("a", "b")
        )
        self.assertRejected(
            "multiple_auth_methods", "invalid_request", data=self.jwt_data(client_secret="s")
        )
        self.assertRejected(
            "multiple_auth_methods",
            "invalid_request",
            data={"client_id": "a", "client_secret": "s"},
            basic=("a", "b"),
        )
        self.assertRejected(
            "client_id_mismatch", "invalid_request", data={"client_id": "c"}, basic=("a", "b")
        )
        self.assertRejected("client_id_mismatch", data=self.jwt_data(client_id="other"))

    def test_malformed(self):
        self.assertRejected("unsupported_assertion_type", data={CLIENT_ASSERTION: self.assertion})
        self.assertRejected(
            "unsupported_assertion_type",
            data=self.jwt_data(
                **{CLIENT_ASSERTION_TYPE: "urn:ietf:params:oauth:grant-type:jwt-bearer"}
            ),
        )
        self.assertRejected(
            "missing_assertion",
            "invalid_request",
            data={CLIENT_ASSERTION_TYPE: CLIENT_ASSERTION_TYPE_JWT},
        )
        self.assertRejected("malformed_assertion", data=self.jwt_data(client_assertion="a.b.c"))
        self.assertRejected("malformed_assertion", data=self.jwt_data(client_assertion="x" * 9000))
        self.assertRejected(
            "duplicate_parameter",
            "invalid_request",
            data={**self.jwt_data(), CLIENT_ASSERTION: [self.assertion, self.assertion]},
        )
        self.assertRejected(
            "credentials_in_query",
            "invalid_request",
            data=self.jwt_data(),
            query=f"?{CLIENT_ASSERTION}=x",
        )
        self.assertRejected("missing_client_id", data={})
        with self.assertRaises(ClientAuthenticationError):
            parse_client_credentials(
                self.factory.post("/token", data={}, HTTP_AUTHORIZATION="Basic !!!")
            )


class TestAuthenticatePrivateKeyJWT(TestCase):
    """Request level private_key_jwt authentication of a resolved client"""

    def setUp(self):
        self.factory = RequestFactory()
        self.key = SigningKey.ec()
        self.keys = StaticClientKeySource((self.key.trusted(),))
        self.provider = OAuth2Provider.objects.create(
            name=generate_id(),
            client_id=CLIENT_ID,
            client_type=ClientType.CONFIDENTIAL,
            authorization_flow=create_test_flow(),
        )
        self.client_ctx = OAuthClientContext.for_provider(self.provider)

    def authenticate(self, data: dict):
        request = self.factory.post("/token", data=data)
        credentials = parse_client_credentials(request)
        client = OAuthClientResolver.legacy().resolve(request, credentials.client_id)
        self.assertEqual(client, self.client_ctx)
        return authenticate_private_key_jwt(credentials, client, self.keys, POLICY)

    def test_authenticate(self):
        auth = self.authenticate(
            {CLIENT_ASSERTION_TYPE: CLIENT_ASSERTION_TYPE_JWT, CLIENT_ASSERTION: self.key.sign()}
        )
        self.assertEqual(auth.client, self.client_ctx)
        self.assertEqual(auth.method, ClientAuthMethod.PRIVATE_KEY_JWT)
        self.assertEqual(auth.assertion.client_id, CLIENT_ID)
        self.assertEqual(auth.assertion.key_id, self.key.kid)

    def test_other_methods_rejected(self):
        """A client authenticating with private_key_jwt cannot fall back to a secret or none"""
        for creds in (
            PresentedClientCredentials(ClientAuthMethod.NONE, CLIENT_ID),
            PresentedClientCredentials(
                ClientAuthMethod.CLIENT_SECRET_POST, CLIENT_ID, self.provider.client_secret
            ),
            PresentedClientCredentials(
                ClientAuthMethod.CLIENT_SECRET_BASIC, CLIENT_ID, self.provider.client_secret
            ),
            PresentedClientCredentials(ClientAuthMethod.PRIVATE_KEY_JWT, CLIENT_ID),
        ):
            with self.subTest(method=creds.method):
                with self.assertRaises(ClientAuthenticationError) as ctx:
                    authenticate_private_key_jwt(creds, self.client_ctx, self.keys, POLICY)
                self.assertEqual(ctx.exception.cause, "auth_method_not_allowed")

    def test_client_mismatch(self):
        creds = PresentedClientCredentials(
            ClientAuthMethod.PRIVATE_KEY_JWT, "other", client_assertion=self.key.sign()
        )
        with self.assertRaises(ClientAuthenticationError) as ctx:
            authenticate_private_key_jwt(creds, self.client_ctx, self.keys, POLICY)
        self.assertEqual(ctx.exception.cause, "client_id_mismatch")


class TestClientAssertionReplayConcurrency(TransactionTestCase):
    """Replay protection holds across concurrent database connections, as used by
    separate workers sharing the PostgreSQL cache"""

    WORKERS = 8

    def test_concurrent_replay(self):
        key = SigningKey.ec()
        keys = StaticClientKeySource((key.trusted(),))
        assertion = key.sign()
        barrier = Barrier(self.WORKERS)

        def attempt(_) -> str:
            # Each thread has its own database connection
            try:
                verifier = ClientAssertionVerifier(keys, POLICY)
                barrier.wait()
                verifier.verify(assertion, CLIENT_ID)
                return "ok"
            except ClientAuthenticationError as exc:
                return exc.cause
            finally:
                connection.close()

        with ThreadPoolExecutor(self.WORKERS) as pool:
            results = list(pool.map(attempt, range(self.WORKERS)))
        self.assertEqual(results.count("ok"), 1, results)
        self.assertEqual(results.count("replayed"), self.WORKERS - 1, results)
