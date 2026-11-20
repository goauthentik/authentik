"""JWKS validation"""

from cryptography.hazmat.primitives.asymmetric.rsa import generate_private_key
from django.test import SimpleTestCase
from jwcrypto.jwk import JWK

from authentik.enterprise.providers.oauth2_cimd.errors import InvalidClientKeys
from authentik.enterprise.providers.oauth2_cimd.jwks import validate_jwks
from authentik.enterprise.providers.oauth2_cimd.tests.utils import private_jwk, public_jwk


class TestJWKS(SimpleTestCase):
    """JWKS validation"""

    def assertInvalid(self, jwks, code=None):
        with self.assertRaises(InvalidClientKeys) as ctx:
            validate_jwks(jwks)
        if code:
            self.assertEqual(ctx.exception.code, code)

    def test_valid_key_types(self):
        keys = validate_jwks(
            {
                "keys": [
                    public_jwk("RSA", kid="rsa", alg="PS256", use="sig"),
                    public_jwk("EC", kid="ec", alg="ES256"),
                    public_jwk("OKP", kid="okp", key_ops=["verify"]),
                ]
            }
        )
        self.assertEqual(keys.kids, frozenset(("rsa", "ec", "okp")))
        self.assertEqual(keys.find("rsa").algorithms, frozenset(("PS256",)))
        self.assertEqual(keys.find("ec").algorithms, frozenset(("ES256",)))
        self.assertEqual(keys.find("okp").algorithms, frozenset(("EdDSA",)))
        self.assertIsNone(keys.find("unknown"))
        self.assertIsNone(keys.find(None))
        for key in keys.keys:
            self.assertIsNotNone(key.public_key)
            self.assertEqual(len(key.thumbprint), 43)

    def test_public_members_only(self):
        jwk = public_jwk("RSA", kid="a") | {"x5u": "https://example.com/x", "jku": "https://x"}
        key = validate_jwks({"keys": [jwk]}).find("a")
        self.assertEqual(set(key.jwk), {"kty", "n", "e", "kid"})
        with self.assertRaises(TypeError):
            key.jwk["d"] = "x"  # type: ignore[index]

    def test_single_key_without_kid(self):
        jwk = public_jwk("EC")
        jwk.pop("kid", None)
        keys = validate_jwks({"keys": [jwk]})
        self.assertIsNotNone(keys.find(None))

    def test_private_members(self):
        private = private_jwk("RSA")
        for member in ("d", "p", "q", "dp", "dq", "qi"):
            with self.subTest(member=member):
                self.assertInvalid(
                    {"keys": [public_jwk("RSA") | {member: private[member]}]}, "private_key"
                )
        self.assertInvalid({"keys": [private_jwk("EC")]}, "private_key")
        self.assertInvalid({"keys": [private_jwk("OKP")]}, "private_key")

    def test_private_key_rejects_whole_set(self):
        self.assertInvalid(
            {"keys": [public_jwk("EC", kid="good"), private_jwk("RSA")]}, "private_key"
        )

    def test_private_encryption_key(self):
        """Private material is rejected even on keys that would be skipped"""
        self.assertInvalid({"keys": [private_jwk("RSA") | {"use": "enc"}]}, "private_key")

    def test_symmetric(self):
        oct_key = JWK.generate(kty="oct", size=256).export(as_dict=True)
        self.assertInvalid({"keys": [oct_key]}, "private_key")
        self.assertInvalid({"keys": [{"kty": "oct", "kid": "x"}]}, "symmetric_key")

    def test_malformed(self):
        rsa = public_jwk("RSA")
        ec = public_jwk("EC")
        cases = {
            "not an object": ["key"],
            "no kty": [{"n": rsa["n"], "e": rsa["e"]}],
            "kty type": [rsa | {"kty": 1}],
            "missing n": [{"kty": "RSA", "e": rsa["e"]}],
            "bad base64": [rsa | {"n": "!!!not-base64!!!"}],
            "not on curve": [ec | {"y": ec["x"]}],
            "kid type": [rsa | {"kid": 1}],
            "empty kid": [rsa | {"kid": ""}],
            "key_ops type": [rsa | {"key_ops": "verify"}],
        }
        for name, keys in cases.items():
            with self.subTest(name=name):
                self.assertInvalid({"keys": keys})

    def test_malformed_set(self):
        for jwks in (None, [], "x", {"keys": "x"}, {"keys": {}}, {}):
            with self.subTest(jwks=jwks):
                self.assertInvalid(jwks, "malformed_jwks")

    def test_algorithms(self):
        self.assertInvalid({"keys": [public_jwk("RSA", alg="HS256")]}, "unsupported_alg")
        self.assertInvalid({"keys": [public_jwk("RSA", alg="none")]}, "unsupported_alg")
        self.assertInvalid({"keys": [public_jwk("RSA", alg="ES256")]}, "unsupported_alg")
        self.assertInvalid({"keys": [public_jwk("EC", alg="ES384")]}, "malformed_key")

    def test_curves(self):
        self.assertInvalid({"keys": [public_jwk("EC") | {"crv": "secp256k1"}]}, "unsupported_curve")
        self.assertInvalid({"keys": [public_jwk("OKP") | {"crv": "X25519"}]}, "unsupported_curve")

    def test_weak_rsa(self):
        # Deliberately weak key, to check it is rejected
        small = JWK.from_pyca(generate_private_key(65537, 1024).public_key())  # nosec B505
        self.assertInvalid({"keys": [small.export_public(as_dict=True)]}, "weak_key")

    def test_skipped_keys(self):
        """Encryption keys and unknown key types aren't usable, but aren't errors"""
        keys = validate_jwks(
            {
                "keys": [
                    public_jwk("RSA", kid="enc", use="enc"),
                    public_jwk("RSA", kid="wrap", key_ops=["wrapKey"]),
                    {"kty": "PQC", "kid": "future"},
                    public_jwk("EC", kid="sig"),
                ]
            }
        )
        self.assertEqual(keys.kids, frozenset(("sig",)))

    def test_no_usable_keys(self):
        keys = validate_jwks({"keys": [public_jwk("RSA", use="enc")]})
        self.assertFalse(keys)
        self.assertFalse(validate_jwks({"keys": []}))

    def test_duplicate_kid(self):
        self.assertInvalid(
            {"keys": [public_jwk("RSA", 0, kid="a"), public_jwk("EC", 0, kid="a")]},
            "duplicate_kid",
        )

    def test_too_many_keys(self):
        self.assertInvalid({"keys": [public_jwk("EC")] * 33}, "too_many_keys")
