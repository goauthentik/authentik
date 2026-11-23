"""Client identifier, metadata document and redirect URI validation"""

from dataclasses import FrozenInstanceError

from django.test import SimpleTestCase

from authentik.enterprise.providers.oauth2_cimd.errors import (
    InvalidClientID,
    InvalidClientMetadata,
    UnsupportedClient,
)
from authentik.enterprise.providers.oauth2_cimd.metadata import (
    parse_client_id,
    redirect_uri_allowed,
    validate_metadata,
)
from authentik.enterprise.providers.oauth2_cimd.tests.utils import (
    CLIENT_ID,
    REDIRECT_URI,
    public_document,
)

# Public keys that a crypto-free parser must accept without understanding them
RSA_1024_KEY = {"kty": "RSA", "kid": "small", "e": "AQAB", "n": "x" * 171}
OKP_KEY = {"kty": "OKP", "crv": "Ed25519", "x": "11qYAYKxCrfVS_7TyWQHOg7hcvPapiMlrwIaaPcHURo"}
UNKNOWN_CURVE_KEY = {"kty": "EC", "crv": "secp256k1", "x": "AAAA", "y": "AAAA"}


class TestClientID(SimpleTestCase):
    """Client identifier URL rules (draft -03 section 3, plus local restrictions)"""

    def assertInvalidID(self, client_id, code="invalid_client_id"):
        with self.assertRaises(InvalidClientID) as ctx:
            parse_client_id(client_id)
        self.assertEqual(ctx.exception.code, code)

    def test_valid(self):
        for client_id, host in (
            (CLIENT_ID, "client.example.com"),
            ("https://client.example.com:8443/client.json", "client.example.com"),
            ("https://client.example.com/a/b%20c/client", "client.example.com"),
            ("https://claude.ai/oauth/claude-code-client-metadata", "claude.ai"),
            ("https://vscode.dev/oauth/client-metadata.json", "vscode.dev"),
        ):
            with self.subTest(client_id=client_id):
                identifier = parse_client_id(client_id)
                self.assertEqual(identifier.url, client_id)
                self.assertEqual(identifier.host, host)

    def test_type_and_syntax(self):
        for client_id in (None, 123, b"https://client.example.com/c", "", "client"):
            with self.subTest(client_id=client_id):
                self.assertInvalidID(client_id)

    def test_https(self):
        self.assertInvalidID("http://client.example.com/client.json")
        self.assertInvalidID("HTTPS://client.example.com/client.json")
        self.assertInvalidID("ftp://client.example.com/client.json")

    def test_path(self):
        self.assertInvalidID("https://client.example.com", "path_required")
        self.assertInvalidID("https://client.example.com/", "path_required")

    def test_userinfo(self):
        self.assertInvalidID("https://user:pass@client.example.com/client.json")
        self.assertInvalidID("https://user@client.example.com/client.json")
        self.assertInvalidID("https://@client.example.com/client.json")

    def test_fragment(self):
        self.assertInvalidID("https://client.example.com/client.json#frag")
        self.assertInvalidID("https://client.example.com/client.json#")

    def test_query(self):
        """Allowed by the generic fetcher, refused for client IDs"""
        self.assertInvalidID("https://client.example.com/client.json?version=1", "query")
        self.assertInvalidID("https://client.example.com/client.json?", "query")

    def test_dot_segments(self):
        for client_id in (
            "https://client.example.com/a/../client.json",
            "https://client.example.com/./client.json",
            "https://client.example.com/a/..",
            "https://client.example.com/a/.",
            "https://client.example.com/..",
        ):
            with self.subTest(client_id=client_id):
                self.assertInvalidID(client_id, "dot_segment")
        # Dots inside a segment are fine
        parse_client_id("https://client.example.com/.well-known/client..json")

    def test_unsafe_escapes(self):
        for escape in ("%2e", "%2E", "%2f", "%2F", "%5c", "%5C"):
            with self.subTest(escape=escape):
                self.assertInvalidID(f"https://client.example.com/a{escape}b", "unsafe_escape")
        self.assertInvalidID("https://client.example.com/%2e%2e/client.json", "unsafe_escape")
        # Generic fetcher rules still apply
        self.assertInvalidID("https://client.example.com/a%00b")
        self.assertInvalidID("https://client.example.com/a%zzb")
        self.assertInvalidID("https://client.example.com/a\\b")

    def test_canonical_host(self):
        for client_id in (
            "https://Client.Example.com/client.json",
            "https://client.example.com./client.json",
            "https://client.example.com:443/client.json",
        ):
            with self.subTest(client_id=client_id):
                self.assertInvalidID(client_id, "non_canonical_host")

    def test_length(self):
        self.assertInvalidID("https://client.example.com/" + "a" * 3000)


class TestMetadata(SimpleTestCase):
    """Metadata document validation for public clients"""

    def assertInvalid(self, document, code=None, client_id=CLIENT_ID):
        with self.assertRaises(InvalidClientMetadata) as ctx:
            validate_metadata(document, client_id)
        if code:
            self.assertEqual(ctx.exception.code, code)
        return ctx.exception

    def assertUnsupported(self, document, code):
        with self.assertRaises(UnsupportedClient) as ctx:
            validate_metadata(document, CLIENT_ID)
        self.assertEqual(ctx.exception.code, code)

    def test_valid_public(self):
        metadata = validate_metadata(public_document(scope="openid mcp:tools"), CLIENT_ID)
        self.assertEqual(metadata.client_id, CLIENT_ID)
        self.assertEqual(metadata.client_name, "Example MCP client")
        self.assertTrue(metadata.client_name_declared)
        self.assertEqual(metadata.redirect_uris, (REDIRECT_URI,))
        self.assertEqual(metadata.grant_types, ("authorization_code", "refresh_token"))
        self.assertEqual(metadata.scopes, ("openid", "mcp:tools"))
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

    def test_client_id_rules_applied(self):
        """The URL rules hold even when the document matches the URL"""
        client_id = CLIENT_ID + "?v=1"
        with self.assertRaises(InvalidClientID):
            validate_metadata(public_document(client_id=client_id), client_id)

    def test_defaults(self):
        """RFC 7591 grant/response defaults, draft -03 `none` default"""
        metadata = validate_metadata(
            {"client_id": CLIENT_ID, "redirect_uris": [REDIRECT_URI]}, CLIENT_ID
        )
        self.assertEqual(metadata.grant_types, ("authorization_code",))
        self.assertIsNone(metadata.scopes)

    def test_client_name_fallback(self):
        """Without client_name, the client ID's host is shown, and recorded as such"""
        metadata = validate_metadata(public_document(client_name=None), CLIENT_ID)
        self.assertEqual(metadata.client_name, "client.example.com")
        self.assertFalse(metadata.client_name_declared)

    def test_field_types(self):
        cases = {
            "client_name": [1, ["a"], {"a": 1}, True, "", "x" * 300, "a\nb", "a\u202eb"],
            "redirect_uris": ["http://127.0.0.1/cb", [1], [None], {"a": 1}, [""]],
            "grant_types": ["authorization_code", [1], {}],
            "response_types": ["code", [True]],
            "token_endpoint_auth_method": [["none"], 1, ""],
            "scope": [["openid"], 1, "a  b", 'bad"scope', ""],
            "jwks_uri": [1, ["x"]],
            "client_uri": [1],
            "policy_uri": [["https://x"]],
            "tos_uri": [{"a": 1}],
        }
        for field, values in cases.items():
            for value in values:
                with self.subTest(field=field, value=value):
                    self.assertInvalid(public_document(**{field: value}))

    def test_auth_method_none_only(self):
        self.assertUnsupported(
            public_document(token_endpoint_auth_method="private_key_jwt"),
            "auth_method_unsupported",
        )
        self.assertUnsupported(
            public_document(token_endpoint_auth_method="tls_client_auth"),
            "auth_method_unsupported",
        )

    def test_shared_secret_methods(self):
        for method in ("client_secret_basic", "client_secret_post", "client_secret_jwt"):
            with self.subTest(method=method):
                self.assertInvalid(
                    public_document(token_endpoint_auth_method=method), "shared_secret"
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
        """Unknown fields, and logo_uri, are not exposed on the typed result"""
        metadata = validate_metadata(
            public_document(
                roles=["admin"],
                is_superuser=True,
                software_statement="eyJ...",
                logo_uri="https://client.example.com/logo.png",
                token_endpoint_auth_methods_supported=["private_key_jwt"],
            ),
            CLIENT_ID,
        )
        for name in ("roles", "is_superuser", "software_statement", "logo_uri"):
            self.assertFalse(hasattr(metadata, name))
            self.assertFalse(hasattr(metadata.to_client(expires_at=0, stale=False), name))

    def test_grants_narrowed(self):
        """Grants outside the public profile are dropped, never granted"""
        metadata = validate_metadata(
            public_document(
                grant_types=[
                    "client_credentials",
                    "authorization_code",
                    "urn:ietf:params:oauth:grant-type:device_code",
                    "implicit",
                    "refresh_token",
                ],
                response_types=["token", "code"],
            ),
            CLIENT_ID,
        )
        self.assertEqual(metadata.grant_types, ("authorization_code", "refresh_token"))
        metadata = validate_metadata(public_document(grant_types=["authorization_code"]), CLIENT_ID)
        self.assertEqual(metadata.grant_types, ("authorization_code",))

    def test_authorization_code_required(self):
        for grants, responses in (
            (["refresh_token"], ["code"]),
            (["client_credentials"], ["code"]),
            ([], ["code"]),
            (["authorization_code"], ["token"]),
            (["authorization_code"], []),
        ):
            with self.subTest(grants=grants, responses=responses):
                self.assertUnsupported(
                    public_document(grant_types=grants, response_types=responses),
                    "authorization_code_required",
                )

    def test_redirect_uris_required(self):
        self.assertUnsupported(public_document(redirect_uris=None), "redirect_uris_required")
        self.assertUnsupported(public_document(redirect_uris=[]), "redirect_uris_required")

    def test_keys_crypto_free(self):
        """Public clients don't use keys, so unusual public keys don't matter"""
        for key in (RSA_1024_KEY, OKP_KEY, UNKNOWN_CURVE_KEY, {"kty": "unknown"}, {}):
            with self.subTest(key=key):
                validate_metadata(public_document(jwks={"keys": [key]}), CLIENT_ID)
        validate_metadata(public_document(jwks_uri="https://client.example.com/jwks"), CLIENT_ID)

    def test_jwks_exclusive(self):
        self.assertInvalid(
            public_document(jwks={"keys": [OKP_KEY]}, jwks_uri="https://client.example.com/j"),
            "jwks_conflict",
        )

    def test_jwks_private_or_symmetric(self):
        for member in ("d", "p", "q", "dp", "dq", "qi", "oth", "k"):
            with self.subTest(member=member):
                self.assertInvalid(
                    public_document(jwks={"keys": [RSA_1024_KEY | {member: "AAAA"}]}),
                    "private_key",
                )
        self.assertInvalid(
            public_document(jwks={"keys": [{"kty": "oct", "kid": "x"}]}), "symmetric_key"
        )

    def test_jwks_malformed(self):
        for jwks in ([], "x", {}, {"keys": "x"}, {"keys": ["x"]}, {"keys": [{}] * 33}):
            with self.subTest(jwks=jwks):
                self.assertInvalid(public_document(jwks=jwks), "malformed_jwks")

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
            "http://127.0.0.2/callback",
            "http://LOCALHOST/callback",
            "http://localhost.example.com/callback",
            "HTTP://localhost/callback",
            "https://app.example.com/callback#frag",
            "javascript:alert(1)",
            "data:text/html,x",
            "/relative/path",
            "https://user:pass@app.example.com/cb",
            "https://app.example.com:99999/cb",
            "http://localhost:/cb",
            "https:///nohost",
            "https:/app.example.com/cb",
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
                tos_uri="javascript:alert(1)",
                policy_uri="http://client.example.com/privacy",
            ),
            CLIENT_ID,
        )
        self.assertEqual(metadata.client_uri, "https://client.example.com")
        self.assertIsNone(metadata.tos_uri)
        self.assertIsNone(metadata.policy_uri)


class TestRedirectURIAllowed(SimpleTestCase):
    """Redirect URI matching (decision O1)"""

    CLAUDE_CODE = ("http://localhost/callback", "http://127.0.0.1/callback")
    VSCODE = ("http://127.0.0.1:33418/", "https://vscode.dev/redirect")

    def assertAllowed(self, registered, presented):
        self.assertTrue(redirect_uri_allowed(registered, presented), presented)

    def assertRefused(self, registered, presented):
        self.assertFalse(redirect_uri_allowed(registered, presented), presented)

    def test_claude_code(self):
        """Claude Code registers port-less loopback URIs and listens on an ephemeral port"""
        for uri in (
            "http://localhost:53121/callback",
            "http://localhost/callback",
            "http://127.0.0.1:53121/callback",
            "http://localhost:80/callback",
        ):
            with self.subTest(uri=uri):
                self.assertAllowed(self.CLAUDE_CODE, uri)
        for uri in (
            "http://localhost:1/other",
            "https://localhost:1/callback",
            "http://localhost:53121/callback/",
            "http://localhost:53121/Callback",
            "http://localhost:53121/callback?x=1",
            "http://localhost:53121/callback#x",
            "http://user@localhost:53121/callback",
            "http://LOCALHOST:53121/callback",
            "HTTP://localhost:53121/callback",
            "http://[::1]:53121/callback",
            "http://localhost.example.com:53121/callback",
            "http://localhost:0/callback",
            "http://localhost:99999/callback",
            "http://localhost:/callback",
            "http://localhost:+1/callback",
            "http://localhost:53121",
        ):
            with self.subTest(uri=uri):
                self.assertRefused(self.CLAUDE_CODE, uri)

    def test_vscode(self):
        """VS Code registers a fixed loopback port and an HTTPS redirect"""
        self.assertAllowed(self.VSCODE, "http://127.0.0.1:33418/")
        # O1: any port on a registered loopback URI, as RFC 8252 section 7.3 requires
        self.assertAllowed(self.VSCODE, "http://127.0.0.1:40001/")
        self.assertAllowed(self.VSCODE, "https://vscode.dev/redirect")
        for uri in (
            "http://127.0.0.1:33418/other",
            "http://127.0.0.1:33418",
            "http://localhost:33418/",
            "https://127.0.0.1:33418/",
            "https://vscode.dev:8443/redirect",
            "https://vscode.dev/redirect/",
            "https://vscode.dev/redirect?x=1",
            "https://VSCODE.dev/redirect",
            "http://vscode.dev/redirect",
        ):
            with self.subTest(uri=uri):
                self.assertRefused(self.VSCODE, uri)

    def test_ipv6_loopback(self):
        registered = ("http://[::1]/cb",)
        self.assertAllowed(registered, "http://[::1]:5000/cb")
        self.assertRefused(registered, "http://[::1]x:5000/cb")
        self.assertRefused(registered, "http://[0:0::1]:5000/cb")
        self.assertRefused(registered, "http://127.0.0.1:5000/cb")

    def test_loopback_query(self):
        registered = ("http://127.0.0.1/cb?app=1",)
        self.assertAllowed(registered, "http://127.0.0.1:5000/cb?app=1")
        self.assertRefused(registered, "http://127.0.0.1:5000/cb?app=2")
        self.assertRefused(registered, "http://127.0.0.1:5000/cb")

    def test_non_loopback_exact(self):
        registered = ("https://app.example.com/cb", "com.example.app:/oauth/callback")
        self.assertAllowed(registered, "https://app.example.com/cb")
        self.assertAllowed(registered, "com.example.app:/oauth/callback")
        self.assertRefused(registered, "https://app.example.com:444/cb")
        self.assertRefused(registered, "com.example.app:/oauth/callback2")

    def test_nothing_registered(self):
        self.assertRefused((), "http://localhost:5000/cb")
        self.assertRefused([], "")
