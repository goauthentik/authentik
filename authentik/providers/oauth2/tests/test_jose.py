"""Test shared JOSE primitives"""

import time
from base64 import urlsafe_b64encode
from unittest import skipIf
from unittest.mock import patch

from cryptography.hazmat.backends.openssl.backend import backend
from cryptography.hazmat.primitives.asymmetric.ec import SECP256R1
from cryptography.hazmat.primitives.asymmetric.ec import generate_private_key as generate_ec
from cryptography.hazmat.primitives.asymmetric.ed448 import Ed448PrivateKey
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.asymmetric.mldsa import MLDSA44PrivateKey, MLDSA65PrivateKey
from django.core.cache import caches
from django.db import DatabaseError, transaction
from django.test import TestCase
from jwt import encode
from jwt.algorithms import ECAlgorithm, OKPAlgorithm

from authentik.core.models import User
from authentik.lib.generators import generate_id
from authentik.lib.jwt_mldsa import MLDSAAlgorithm
from authentik.providers.oauth2.client_auth import (
    AssertionAudience,
    ClientAssertionPolicy,
    ClientAssertionVerifier,
    ClientAuthenticationError,
    StaticClientKeySource,
)
from authentik.providers.oauth2.jose import (
    ALGORITHMS,
    DEFAULT_ALGORITHMS,
    InvalidKey,
    TrustedKey,
    asymmetric_algorithms,
    consume_jti,
    jwt_typ_matches,
    parse_jwks,
    usable_algorithms,
)

CLIENT_ID = "https://agent.example/client.json"
ISSUER = "https://authentik.example/application/o/app/"
EXTENSIONS = ("EdDSA", "ML-DSA-44", "ML-DSA-65", "ML-DSA-87")
NO_EXTENSIONS_UNDER_FIPS = skipIf(backend._fips_enabled, "The FIPS provider has no EdDSA/ML-DSA")


def fips(enabled: bool):
    """Simulate OpenSSL running with (or without) the FIPS provider"""
    return patch("authentik.providers.oauth2.jose.fips_enabled", return_value=enabled)


def ed25519_jwk(private=None, **extra) -> dict:
    private = private or Ed25519PrivateKey.generate()
    jwk = OKPAlgorithm.to_jwk(private.public_key(), as_dict=True)
    return {**jwk, "kid": generate_id(), **extra}


def mldsa_jwk(private=None, name="ML-DSA-44", **extra) -> dict:
    private = private or MLDSA44PrivateKey.generate()
    jwk = MLDSAAlgorithm(name).to_jwk(private.public_key(), as_dict=True)
    return {**jwk, "kid": generate_id(), **extra}


def ec_jwk() -> dict:
    jwk = ECAlgorithm.to_jwk(generate_ec(SECP256R1()).public_key(), as_dict=True)
    return {**jwk, "kid": generate_id()}


class TestAlgorithms(TestCase):
    """One asymmetric algorithm set, filtered for FIPS"""

    def test_default(self):
        self.assertLessEqual(DEFAULT_ALGORITHMS, ALGORITHMS.keys())
        self.assertTrue(all(ALGORITHMS[alg].fips for alg in DEFAULT_ALGORITHMS))
        for alg in ("HS256", "HS384", "HS512", "none"):
            self.assertNotIn(alg, ALGORITHMS)
        # Extensions are never accepted by default
        for alg in EXTENSIONS:
            self.assertNotIn(alg, DEFAULT_ALGORITHMS)
        for enabled in (False, True):
            with fips(enabled):
                self.assertEqual(asymmetric_algorithms(), DEFAULT_ALGORITHMS)

    def test_extensions(self):
        with fips(False):
            self.assertEqual(asymmetric_algorithms(*EXTENSIONS), ALGORITHMS.keys())
            self.assertEqual(
                asymmetric_algorithms("EdDSA"), DEFAULT_ALGORITHMS | frozenset({"EdDSA"})
            )
        with fips(True):
            self.assertEqual(asymmetric_algorithms(*EXTENSIONS), DEFAULT_ALGORITHMS)
        for alg in ("HS256", "none", "Ed25519"):
            with self.subTest(alg=alg):
                with self.assertRaises(ValueError):
                    asymmetric_algorithms(alg)

    def test_usable(self):
        with fips(False):
            self.assertEqual(
                usable_algorithms({"ES256", "EdDSA", "HS256", "none", "unknown"}),
                {"ES256", "EdDSA"},
            )
        with fips(True):
            self.assertEqual(usable_algorithms({"ES256", "EdDSA", "ML-DSA-44"}), {"ES256"})


class TestTrustedKey(TestCase):
    """The shared JWK validator, beyond what the client assertion tests cover"""

    @NO_EXTENSIONS_UNDER_FIPS
    def test_eddsa_opt_in(self):
        jwk = ed25519_jwk()
        with self.assertRaises(InvalidKey):
            TrustedKey.from_jwk(jwk)
        key = TrustedKey.from_jwk(jwk, asymmetric_algorithms("EdDSA"))
        self.assertEqual((key.kty, key.crv), ("OKP", "Ed25519"))
        self.assertEqual(set(key.public_jwk), {"crv", "kty", "x"})
        self.assertTrue(key.supports("EdDSA"))
        self.assertFalse(key.supports("ES256"))
        self.assertEqual(
            key.thumbprint,
            TrustedKey.from_jwk({**jwk, "x5u": "https://x"}, {"EdDSA"}).thumbprint,
        )
        # Ed448 is EdDSA too, but not accepted
        ed448 = OKPAlgorithm.to_jwk(Ed448PrivateKey.generate().public_key(), as_dict=True)
        with self.assertRaises(InvalidKey):
            TrustedKey.from_jwk(ed448, {"EdDSA"})
        with self.assertRaises(InvalidKey):
            TrustedKey.from_jwk(ed25519_jwk(alg="ES256"), {"EdDSA", "ES256"})
        with self.assertRaises(InvalidKey):
            TrustedKey.from_jwk({**jwk, "d": "AAAA"}, {"EdDSA"})

    @NO_EXTENSIONS_UNDER_FIPS
    def test_mldsa_opt_in(self):
        jwk = mldsa_jwk()
        with self.assertRaises(InvalidKey):
            TrustedKey.from_jwk(jwk)
        key = TrustedKey.from_jwk(jwk, {"ML-DSA-44"})
        self.assertEqual((key.kty, key.alg), ("AKP", "ML-DSA-44"))
        self.assertTrue(key.supports("ML-DSA-44"))
        self.assertFalse(key.supports("ML-DSA-65"))
        for bad in (
            # RFC 9964: alg is required on AKP keys
            {k: v for k, v in jwk.items() if k != "alg"},
            # Only the opted in parameter sets
            mldsa_jwk(MLDSA65PrivateKey.generate(), "ML-DSA-65"),
            # Key material of another parameter set
            {**mldsa_jwk(MLDSA65PrivateKey.generate(), "ML-DSA-65"), "alg": "ML-DSA-44"},
            {**jwk, "priv": "AAAA"},
        ):
            with self.subTest(jwk=bad):
                with self.assertRaises(InvalidKey):
                    TrustedKey.from_jwk(bad, {"ML-DSA-44"})

    def test_fips_filters_keys(self):
        """Keys only usable with algorithms FIPS mode can't verify are skipped"""
        ec, okp, akp = ec_jwk(), ed25519_jwk(), mldsa_jwk()
        with fips(True):
            keys = parse_jwks({"keys": [ec, okp, akp]}, asymmetric_algorithms(*EXTENSIONS))
            self.assertEqual([key.kid for key in keys], [ec["kid"]])
            with self.assertRaises(InvalidKey):
                TrustedKey.from_jwk(okp, {"EdDSA"})

    @NO_EXTENSIONS_UNDER_FIPS
    def test_parse_jwks_extensions(self):
        ec, okp, akp = ec_jwk(), ed25519_jwk(), mldsa_jwk()
        keys = parse_jwks({"keys": [ec, okp, akp]})
        self.assertEqual([key.kid for key in keys], [ec["kid"]])
        keys = parse_jwks({"keys": [ec, okp, akp]}, asymmetric_algorithms(*EXTENSIONS))
        self.assertEqual([key.kid for key in keys], [ec["kid"], okp["kid"], akp["kid"]])
        with self.assertRaises(InvalidKey):
            parse_jwks({"keys": [ec, {**akp, "priv": "AAAA"}]}, {"ML-DSA-44"})


class TestJWTTypMatches(TestCase):
    """RFC 7515 section 4.1.9 typ comparison"""

    def test_matches(self):
        for typ, accepted in (
            ("JWT", ("JWT",)),
            ("jwt", ("JWT",)),
            ("application/jwt", ("JWT",)),
            ("Application/JWT", ("jwt",)),
            ("JWT", ("application/jwt",)),
            ("oauth-id-jag+jwt", ("oauth-id-jag+jwt",)),
            ("application/OAUTH-ID-JAG+JWT", ("oauth-id-jag+jwt",)),
            ("client-authentication+jwt", ("JWT", "client-authentication+jwt")),
        ):
            with self.subTest(typ=typ, accepted=accepted):
                self.assertTrue(jwt_typ_matches(typ, *accepted))

    def test_no_match(self):
        for typ, accepted in (
            (None, ("JWT",)),
            ("", ("JWT",)),
            (1, ("JWT",)),
            (["JWT"], ("JWT",)),
            ("at+jwt", ("JWT",)),
            ("dpop+jwt", ("JWT", "client-authentication+jwt")),
            ("text/jwt", ("JWT",)),
            ("application/jwt; charset=utf-8", ("JWT",)),
            ("application/", ("JWT",)),
            ("JWT", ()),
        ):
            with self.subTest(typ=typ, accepted=accepted):
                self.assertFalse(jwt_typ_matches(typ, *accepted))


class TestConsumeJTI(TestCase):
    """Shared single-use record for JWT ids"""

    def test_single_use(self):
        jti, until = generate_id(), time.time() + 60
        self.assertTrue(consume_jti("test", CLIENT_ID, jti, until))
        self.assertFalse(consume_jti("test", CLIENT_ID, jti, until))
        # jti values are unique per issuer, and records are per purpose
        self.assertTrue(consume_jti("test", "https://other.example", jti, until))
        self.assertTrue(consume_jti("other", CLIENT_ID, jti, until))
        # No ambiguity from joining the parts
        self.assertTrue(consume_jti("a", "b/c", "d", until))
        self.assertTrue(consume_jti("a", "b", "c/d", until))

    def test_record(self):
        """Only a hash is stored, for as long as asked plus a small margin"""
        jti = generate_id()
        cache = caches["default"]
        with patch.object(cache, "add", wraps=cache.add) as add:
            consume_jti("test", CLIENT_ID, jti, time.time() + 90)
        key, value = add.call_args.args
        self.assertNotIn(jti, key)
        self.assertNotIn(CLIENT_ID, key)
        self.assertIs(value, True)
        self.assertTrue(85 <= add.call_args.kwargs["timeout"] <= 96)  # noqa: PLR2004
        # Already past: still recorded briefly
        with patch.object(cache, "add", wraps=cache.add) as add:
            consume_jti("test", CLIENT_ID, generate_id(), time.time() - 60)
        self.assertGreaterEqual(add.call_args.kwargs["timeout"], 1)

    def test_fails_closed(self):
        cache = caches["default"]
        until = time.time() + 60
        with patch.object(cache, "_cursor", side_effect=DatabaseError):
            self.assertFalse(consume_jti("test", CLIENT_ID, generate_id(), until))
        with patch.object(cache, "add", side_effect=DatabaseError):
            self.assertFalse(consume_jti("test", CLIENT_ID, generate_id(), until))

    def test_outer_transaction_survives(self):
        """A failed record doesn't break the caller's transaction"""
        with transaction.atomic():
            with patch.object(caches["default"], "add", side_effect=DatabaseError):
                self.assertFalse(consume_jti("test", CLIENT_ID, generate_id(), time.time() + 60))
            User.objects.count()


class TestVerifierAlgorithms(TestCase):
    """Client assertions with algorithms a caller opted into, and FIPS filtering"""

    def setUp(self):
        self.private = Ed25519PrivateKey.generate()
        self.jwk = ed25519_jwk(self.private)
        self.policy = ClientAssertionPolicy(
            audience=AssertionAudience(ISSUER),
            # Named explicitly, so FIPS filtering happens in the verifier
            algorithms=DEFAULT_ALGORITHMS | {"EdDSA"},
        )

    def sign(self, private, alg: str, kid: str) -> str:
        now = int(time.time())
        return encode(
            {
                "iss": CLIENT_ID,
                "sub": CLIENT_ID,
                "aud": ISSUER,
                "iat": now,
                "exp": now + 60,
                "jti": generate_id(),
            },
            private,
            algorithm=alg,
            headers={"kid": kid},
        )

    @NO_EXTENSIONS_UNDER_FIPS
    def test_eddsa(self):
        keys = StaticClientKeySource((TrustedKey.from_jwk(self.jwk, self.policy.algorithms),))
        verified = ClientAssertionVerifier(keys, self.policy).verify(
            self.sign(self.private, "EdDSA", self.jwk["kid"]), CLIENT_ID
        )
        self.assertEqual(verified.algorithm, "EdDSA")
        # Without the opt in, EdDSA is not accepted even with a trusted EdDSA key
        default = ClientAssertionPolicy(audience=AssertionAudience(ISSUER))
        with self.assertRaises(ClientAuthenticationError) as ctx:
            ClientAssertionVerifier(keys, default).verify(
                self.sign(self.private, "EdDSA", self.jwk["kid"]), CLIENT_ID
            )
        self.assertEqual(ctx.exception.cause, "unsupported_algorithm")

    @NO_EXTENSIONS_UNDER_FIPS
    def test_mldsa(self):
        private = MLDSA44PrivateKey.generate()
        jwk = mldsa_jwk(private)
        policy = ClientAssertionPolicy(
            audience=AssertionAudience(ISSUER), algorithms=asymmetric_algorithms("ML-DSA-44")
        )
        keys = StaticClientKeySource((TrustedKey.from_jwk(jwk, policy.algorithms),))
        verified = ClientAssertionVerifier(keys, policy).verify(
            self.sign(private, "ML-DSA-44", jwk["kid"]), CLIENT_ID
        )
        self.assertEqual(verified.algorithm, "ML-DSA-44")

    def test_fips_refuses_extensions(self):
        """In FIPS mode, an algorithm the policy names but OpenSSL can't verify is refused
        before any key is used"""

        class Keys:
            def get_keys(self, *, refresh=False):
                raise AssertionError("keys must not be consulted")

        with fips(True):
            verifier = ClientAssertionVerifier(Keys(), self.policy)
            # The header is checked before the signature
            _, payload, signature = encode({"iss": CLIENT_ID}, "x" * 32).split(".")
            header = urlsafe_b64encode(b'{"alg":"EdDSA","kid":"k"}').rstrip(b"=").decode()
            assertion = f"{header}.{payload}.{signature}"
            with self.assertRaises(ClientAuthenticationError) as ctx:
                verifier.verify(assertion, CLIENT_ID)
        self.assertEqual(ctx.exception.cause, "unsupported_algorithm")
