"""Metadata document validation"""

from dataclasses import FrozenInstanceError

from django.test import SimpleTestCase

from authentik.enterprise.providers.oauth2_cimd.errors import (
    InvalidClientID,
    InvalidClientKeys,
    InvalidClientMetadata,
)
from authentik.enterprise.providers.oauth2_cimd.metadata import (
    validate_client_id,
    validate_metadata,
)
from authentik.enterprise.providers.oauth2_cimd.tests.utils import (
    CLIENT_ID,
    JWKS_URI,
    REDIRECT_URI,
    public_document,
    public_jwk,
)


class TestClientID(SimpleTestCase):
    """Client identifier URL rules (draft -03 section 3)"""

    def test_valid(self):
        self.assertEqual(validate_client_id(CLIENT_ID), CLIENT_ID)

    def test_invalid(self):
        for client_id in (
            None,
            123,
            "",
            "client",
            "http://client.example.com/client.json",
            "https://client.example.com",
            "https://client.example.com/",
            "https://user:pass@client.example.com/client.json",
            "https://client.example.com/client.json#frag",
            "https://client.example.com/a/../client.json",
            "https://client.example.com/./client.json",
            "https://client.example.com/client.json?version=1",
            "https://client.example.com/" + "a" * 3000,
        ):
            with self.subTest(client_id=client_id), self.assertRaises(InvalidClientID):
                validate_client_id(client_id)


class TestMetadata(SimpleTestCase):
    """Metadata document validation"""

    def assertInvalid(self, document, code=None, client_id=CLIENT_ID):
        with self.assertRaises(InvalidClientMetadata) as ctx:
            validate_metadata(document, client_id)
        if code:
            self.assertEqual(ctx.exception.code, code)
        return ctx.exception

    def test_valid_public(self):
        metadata = validate_metadata(public_document(scope="openid mcp:tools"), CLIENT_ID)
        self.assertEqual(metadata.client_id, CLIENT_ID)
        self.assertEqual(metadata.client_name, "Example MCP client")
        self.assertEqual(metadata.redirect_uris, (REDIRECT_URI,))
        self.assertEqual(metadata.grant_types, ("authorization_code", "refresh_token"))
        self.assertEqual(metadata.response_types, ("code",))
        self.assertEqual(metadata.token_endpoint_auth_methods, ("none",))
        self.assertEqual(metadata.scopes, frozenset(("openid", "mcp:tools")))
        self.assertFalse(metadata.has_keys)
        with self.assertRaises(FrozenInstanceError):
            metadata.client_name = "x"  # type: ignore[misc]

    def test_exact_client_id(self):
        for value in (
            None,
            CLIENT_ID + "/",
            CLIENT_ID.upper(),
            CLIENT_ID.replace("client.example.com", "client.example.com:443"),
            CLIENT_ID.replace("https://", "HTTPS://"),
            "https://other.example.com/oauth/client.json",
            [CLIENT_ID],
        ):
            with self.subTest(value=value):
                self.assertInvalid(public_document(client_id=value), "client_id_mismatch")
        document = public_document()
        del document["client_id"]
        self.assertInvalid(document, "client_id_mismatch")

    def test_defaults(self):
        """RFC 7591 grant/response defaults, draft -03 `none` default"""
        document = {"client_id": CLIENT_ID, "redirect_uris": [REDIRECT_URI]}
        metadata = validate_metadata(document, CLIENT_ID)
        self.assertEqual(metadata.grant_types, ("authorization_code",))
        self.assertEqual(metadata.response_types, ("code",))
        self.assertEqual(metadata.token_endpoint_auth_methods, ("none",))
        self.assertIsNone(metadata.scopes)
        self.assertIsNone(metadata.client_name)

    def test_field_types(self):
        cases = {
            "client_name": [1, ["a"], {"a": 1}, True, "", "x" * 300, "a\nb"],
            "redirect_uris": ["http://127.0.0.1/cb", [1], [None], {"a": 1}, [""]],
            "grant_types": ["authorization_code", [1], {}],
            "response_types": ["code", [True]],
            "token_endpoint_auth_method": [["none"], 1, ""],
            "token_endpoint_auth_methods_supported": ["none", [1], []],
            "scope": [["openid"], 1, "a  b", 'bad"scope', ""],
            "jwks_uri": [1, ["x"]],
            "token_endpoint_auth_signing_alg": [1, "HS256", "none"],
            "dpop_bound_access_tokens": ["true", 1],
            "software_id": [1],
            "software_version": [["1"]],
            "client_uri": [1],
            "logo_uri": [{"a": 1}],
        }
        for field, values in cases.items():
            for value in values:
                with self.subTest(field=field, value=value):
                    self.assertInvalid(public_document(**{field: value}))

    def test_auth_method_singular(self):
        metadata = validate_metadata(
            public_document(token_endpoint_auth_method="private_key_jwt", jwks_uri=JWKS_URI),
            CLIENT_ID,
        )
        self.assertEqual(metadata.token_endpoint_auth_methods, ("private_key_jwt",))

    def test_auth_method_plural(self):
        metadata = validate_metadata(
            public_document(
                token_endpoint_auth_method=None,
                token_endpoint_auth_methods_supported=["private_key_jwt", "none", "none"],
            ),
            CLIENT_ID,
        )
        self.assertEqual(metadata.token_endpoint_auth_methods, ("private_key_jwt", "none"))

    def test_auth_method_both_consistent(self):
        """Plural list wins; the singular value must be in it"""
        metadata = validate_metadata(
            public_document(
                token_endpoint_auth_method="none",
                token_endpoint_auth_methods_supported=["private_key_jwt", "none"],
            ),
            CLIENT_ID,
        )
        self.assertEqual(metadata.token_endpoint_auth_methods, ("private_key_jwt", "none"))

    def test_auth_method_both_conflict(self):
        self.assertInvalid(
            public_document(
                token_endpoint_auth_method="none",
                token_endpoint_auth_methods_supported=["private_key_jwt"],
            ),
            "auth_method_conflict",
        )

    def test_unknown_auth_method_kept(self):
        """Unknown methods are declared but dropped later, in negotiation"""
        metadata = validate_metadata(
            public_document(
                token_endpoint_auth_method=None,
                token_endpoint_auth_methods_supported=["tls_client_auth", "none"],
            ),
            CLIENT_ID,
        )
        self.assertEqual(metadata.token_endpoint_auth_methods, ("tls_client_auth", "none"))

    def test_shared_secret_methods(self):
        for method in ("client_secret_basic", "client_secret_post", "client_secret_jwt"):
            with self.subTest(method=method):
                self.assertInvalid(
                    public_document(token_endpoint_auth_method=method), "shared_secret"
                )
                self.assertInvalid(
                    public_document(
                        token_endpoint_auth_method=None,
                        token_endpoint_auth_methods_supported=["none", method],
                    ),
                    "shared_secret",
                )

    def test_shared_secret_fields(self):
        self.assertInvalid(public_document(client_secret="hunter2"), "shared_secret")
        self.assertInvalid(public_document(client_secret_expires_at=0), "shared_secret")

    def test_secret_value_not_in_error(self):
        exc = self.assertInvalid(public_document(client_secret="hunter2-secret-value"))
        self.assertNotIn("hunter2", str(exc))

    def test_local_authority_fields(self):
        for field in (
            "registration_access_token",
            "registration_client_uri",
            "authentik_groups",
            "goauthentik.io/user",
        ):
            with self.subTest(field=field):
                self.assertInvalid(public_document(**{field: "x"}), "local_authority")

    def test_unknown_fields_ignored(self):
        """Unknown fields are not exposed on the typed result"""
        metadata = validate_metadata(
            public_document(roles=["admin"], is_superuser=True, software_statement="eyJ..."),
            CLIENT_ID,
        )
        self.assertFalse(hasattr(metadata, "roles"))
        self.assertFalse(hasattr(metadata, "is_superuser"))
        self.assertFalse(hasattr(metadata, "software_statement"))

    def test_jwks_exclusive(self):
        self.assertInvalid(
            public_document(jwks={"keys": [public_jwk()]}, jwks_uri=JWKS_URI), "jwks_conflict"
        )

    def test_inline_jwks(self):
        metadata = validate_metadata(public_document(jwks={"keys": [public_jwk()]}), CLIENT_ID)
        self.assertIsNotNone(metadata.jwks)
        self.assertEqual(len(metadata.jwks.keys), 1)
        self.assertTrue(metadata.has_keys)

    def test_inline_jwks_private(self):
        jwk = public_jwk() | {"d": "AAAA"}
        with self.assertRaises(InvalidClientKeys):
            validate_metadata(public_document(jwks={"keys": [jwk]}), CLIENT_ID)

    def test_jwks_uri(self):
        metadata = validate_metadata(public_document(jwks_uri=JWKS_URI), CLIENT_ID)
        self.assertEqual(metadata.jwks_uri, JWKS_URI)
        self.assertTrue(metadata.has_keys)
        for uri in (
            "http://client.example.com/jwks.json",
            "https://client.example.com/jwks.json?x=1",
            "https://user@client.example.com/jwks.json",
            "not a url",
        ):
            with self.subTest(uri=uri):
                self.assertInvalid(public_document(jwks_uri=uri), "invalid_jwks_uri")

    def test_redirect_uris(self):
        valid = [
            "http://127.0.0.1/callback",
            "http://127.0.0.1:33418/callback",
            "http://[::1]/callback",
            "http://localhost:8080/callback",
            "https://app.example.com/callback",
            "https://app.example.com/callback?query=1",
            "com.example.app:/oauth/callback",
            "cursor://anysphere.cursor-retrieval/oauth/callback",
        ]
        metadata = validate_metadata(public_document(redirect_uris=valid), CLIENT_ID)
        self.assertEqual(metadata.redirect_uris, tuple(valid))
        invalid = [
            "http://app.example.com/callback",
            "https://app.example.com/callback#frag",
            "javascript:alert(1)",
            "data:text/html,x",
            "/relative/path",
            "https://user:pass@app.example.com/cb",
            "https://app.example.com:99999/cb",
            "https:///nohost",
            "https://app.example.com/ space",
        ]
        for uri in invalid:
            with self.subTest(uri=uri):
                self.assertInvalid(public_document(redirect_uris=[uri]), "invalid_redirect_uri")

    def test_redirect_uris_bounded(self):
        uris = [f"http://127.0.0.1/cb{i}" for i in range(33)]
        self.assertInvalid(public_document(redirect_uris=uris))

    def test_informative_uris(self):
        metadata = validate_metadata(
            public_document(
                client_uri="https://client.example.com",
                logo_uri="http://client.example.com/logo.png",
                tos_uri="javascript:alert(1)",
                policy_uri="https://client.example.com/privacy",
            ),
            CLIENT_ID,
        )
        self.assertEqual(metadata.client_uri, "https://client.example.com")
        self.assertIsNone(metadata.logo_uri)
        self.assertIsNone(metadata.tos_uri)
        self.assertEqual(metadata.policy_uri, "https://client.example.com/privacy")

    def test_optional_fields(self):
        metadata = validate_metadata(
            public_document(
                token_endpoint_auth_signing_alg="ES256",
                dpop_bound_access_tokens=True,
                software_id="example",
                software_version="1.2.3",
            ),
            CLIENT_ID,
        )
        self.assertEqual(metadata.token_endpoint_auth_signing_alg, "ES256")
        self.assertTrue(metadata.dpop_bound_access_tokens)
        self.assertEqual(metadata.software_id, "example")
        self.assertEqual(metadata.software_version, "1.2.3")
