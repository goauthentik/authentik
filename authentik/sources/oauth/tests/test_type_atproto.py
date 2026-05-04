"""AT Protocol OAuth Source tests"""

from urllib.parse import parse_qs, urlparse

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.serialization import Encoding, NoEncryption, PrivateFormat
from django.test import RequestFactory, SimpleTestCase
from jwt import decode, get_unverified_header
from requests_mock import Mocker

from authentik.sources.oauth.api.source import OAuthSourceSerializer
from authentik.sources.oauth.models import OAuthSource
from authentik.sources.oauth.types.atproto import (
    BSKY_AUTHORIZATION_URL_DEFAULT,
    BSKY_PAR_URL_DEFAULT,
    BSKY_PUBLIC_PROFILE_URL_DEFAULT,
    BSKY_TOKEN_URL_DEFAULT,
    AtProtoOAuthClient,
    AtProtoType,
)

ATPROTO_DID = "did:plc:z72i7hdynmk6r22z27h6tvur"
ATPROTO_PDS = "https://puffball.us-east.host.bsky.network"
ATPROTO_CLIENT_ID = "https://authentik.example/application/o/atproto/client-metadata.json"

ATPROTO_DID_DOCUMENT = {
    "id": ATPROTO_DID,
    "alsoKnownAs": ["at://bsky.app"],
    "service": [
        {
            "id": "#atproto_pds",
            "type": "AtprotoPersonalDataServer",
            "serviceEndpoint": ATPROTO_PDS,
        }
    ],
}

ATPROTO_PROFILE = {
    "did": ATPROTO_DID,
    "handle": "bsky.app",
    "displayName": "Bluesky",
}
CUSTOM_ISSUER = "https://auth.example"
CUSTOM_AUTHORIZATION_URL = f"{CUSTOM_ISSUER}/oauth/authorize"
CUSTOM_PAR_URL = f"{CUSTOM_ISSUER}/oauth/par"
CUSTOM_TOKEN_URL = f"{CUSTOM_ISSUER}/oauth/token"
CUSTOM_PROFILE_URL = f"{CUSTOM_ISSUER}/xrpc/app.bsky.actor.getProfile"


def private_key_pem() -> str:
    """Generate an ES256 private key for DPoP tests."""
    return (
        ec.generate_private_key(ec.SECP256R1())
        .private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption())
        .decode()
    )


class TestTypeAtProto(SimpleTestCase):
    """AT Protocol OAuth Source tests"""

    def setUp(self):
        self.source = OAuthSource(
            name="test",
            slug="test",
            provider_type="atproto",
            consumer_key=ATPROTO_CLIENT_ID,
        )
        self.factory = RequestFactory()

    def get_request(self):
        request = self.factory.get("/")
        request.session = {}
        return request

    def get_callback_request(self, issuer: str = "https://bsky.social"):
        request = self.factory.get(f"/?state=state&iss={issuer}&code=code")
        request.session = {
            "authentik/sources/oauth/atproto/test": {
                "state": "state",
                "code_verifier": "verifier",
                "issuer": issuer,
                "private_key": private_key_pem(),
                "dpop_nonce": "nonce-1",
                "login_hint": None,
                "expected_did": None,
            }
        }
        return request

    def test_enroll_context(self):
        """Test AT Protocol enrollment context."""
        ak_context = AtProtoType().get_base_user_properties(
            source=self.source,
            info=ATPROTO_PROFILE,
        )
        self.assertEqual(ak_context["username"], ATPROTO_PROFILE["handle"])
        self.assertEqual(ak_context["name"], ATPROTO_PROFILE["displayName"])
        self.assertIsNone(ak_context["email"])

    def test_serializer_allows_missing_secret(self):
        """Test AT Protocol sources can be created without a client secret."""
        serializer = OAuthSourceSerializer()
        validated = serializer.validate(
            {
                "name": "test-atproto",
                "slug": "test-atproto",
                "provider_type": "atproto",
                "consumer_key": ATPROTO_CLIENT_ID,
            }
        )
        self.assertEqual(validated["consumer_secret"], "")

    @Mocker()
    def test_redirect_uses_par_dpop_pkce_and_no_secret(self, mock: Mocker):
        """Test authorization starts with a DPoP-bound pushed authorization request."""
        mock.post(
            BSKY_PAR_URL_DEFAULT,
            json={"request_uri": "urn:request:123"},
            headers={"DPoP-Nonce": "nonce-1"},
        )

        request = self.get_request()
        client = AtProtoOAuthClient(self.source, request, callback="/callback/")
        redirect_url = client.get_redirect_url({"scope": ["atproto", "transition:generic"]})

        parsed_redirect = urlparse(redirect_url)
        parsed_query = parse_qs(parsed_redirect.query)
        parsed_redirect_url = (
            f"{parsed_redirect.scheme}://{parsed_redirect.netloc}{parsed_redirect.path}"
        )
        self.assertEqual(parsed_redirect_url, BSKY_AUTHORIZATION_URL_DEFAULT)
        self.assertEqual(parsed_query["client_id"], [ATPROTO_CLIENT_ID])
        self.assertEqual(parsed_query["request_uri"], ["urn:request:123"])
        self.assertEqual(len(mock.request_history), 1)
        par_request = mock.request_history[0]
        self.assertIn("DPoP", par_request.headers)
        self.assertEqual(par_request.text.count("client_secret"), 0)
        self.assertIn("client_id=https%3A%2F%2Fauthentik.example", par_request.text)
        self.assertIn("code_challenge_method=S256", par_request.text)
        self.assertIn("scope=atproto+transition%3Ageneric", par_request.text)

        header = get_unverified_header(par_request.headers["DPoP"])
        payload = decode(par_request.headers["DPoP"], options={"verify_signature": False})
        self.assertEqual(header["typ"], "dpop+jwt")
        self.assertEqual(header["alg"], "ES256")
        self.assertEqual(payload["htm"], "POST")
        self.assertEqual(payload["htu"], BSKY_PAR_URL_DEFAULT)

    @Mocker()
    def test_custom_urls_override_bluesky_defaults(self, mock: Mocker):
        """Test non-Bluesky AT Protocol endpoint configuration."""
        source = OAuthSource(
            name="test",
            slug="test",
            provider_type="atproto",
            consumer_key=ATPROTO_CLIENT_ID,
            authorization_url=CUSTOM_AUTHORIZATION_URL,
            request_token_url=CUSTOM_PAR_URL,
            access_token_url=CUSTOM_TOKEN_URL,
            profile_url=CUSTOM_PROFILE_URL,
        )
        mock.post(
            CUSTOM_PAR_URL,
            json={"request_uri": "urn:request:custom"},
            headers={"DPoP-Nonce": "nonce-custom"},
        )

        request = self.get_request()
        client = AtProtoOAuthClient(source, request, callback="/callback/")
        redirect_url = client.get_redirect_url({"scope": ["atproto"]})

        parsed_redirect = urlparse(redirect_url)
        self.assertEqual(
            f"{parsed_redirect.scheme}://{parsed_redirect.netloc}{parsed_redirect.path}",
            CUSTOM_AUTHORIZATION_URL,
        )
        self.assertEqual(request.session[client.session_key]["issuer"], CUSTOM_ISSUER)
        self.assertEqual(mock.request_history[0].url, CUSTOM_PAR_URL)

    @Mocker()
    def test_access_token_validates_subject_scope_and_issuer(self, mock: Mocker):
        """Test callback token response validation."""
        mock.post(
            BSKY_TOKEN_URL_DEFAULT,
            json={
                "access_token": "access",
                "refresh_token": "refresh",
                "token_type": "DPoP",
                "expires_in": 300,
                "sub": ATPROTO_DID,
                "scope": "atproto transition:generic",
            },
            headers={"DPoP-Nonce": "nonce-2"},
        )
        mock.get(f"https://plc.directory/{ATPROTO_DID}", json=ATPROTO_DID_DOCUMENT)
        mock.get(
            f"{ATPROTO_PDS}/.well-known/oauth-protected-resource",
            json={"authorization_servers": ["https://bsky.social"]},
        )

        request = self.get_callback_request()

        client = AtProtoOAuthClient(self.source, request, callback="/callback/")
        token = client.get_access_token()

        self.assertEqual(token["sub"], ATPROTO_DID)
        self.assertEqual(token["pds_url"], ATPROTO_PDS)
        token_request = mock.request_history[0]
        self.assertIn("DPoP", token_request.headers)
        self.assertEqual(token_request.text.count("client_secret"), 0)
        self.assertIn("code_verifier=verifier", token_request.text)

    @Mocker()
    def test_access_token_rejects_non_dpop_token_type(self, mock: Mocker):
        """Test callback rejects token responses that are not DPoP-bound."""
        mock.post(
            BSKY_TOKEN_URL_DEFAULT,
            json={
                "access_token": "access",
                "token_type": "Bearer",
                "sub": ATPROTO_DID,
                "scope": "atproto",
            },
            headers={"DPoP-Nonce": "nonce-2"},
        )

        client = AtProtoOAuthClient(self.source, self.get_callback_request(), callback="/callback/")
        token = client.get_access_token()

        self.assertEqual(token["error"], "Token response did not include a DPoP token type.")

    @Mocker()
    def test_did_web_localhost_uses_http_for_local_testing(self, mock: Mocker):
        """Test did:web localhost resolution for the local AT Protocol simulator."""
        mock.get("http://localhost:8787/.well-known/did.json", json={"id": "did:web:localhost"})
        client = AtProtoOAuthClient(self.source, self.get_request(), callback="/callback/")
        document = client.get_did_document("did:web:localhost%3A8787")
        self.assertEqual(document["id"], "did:web:localhost")

    @Mocker()
    def test_profile_info(self, mock: Mocker):
        """Test public Bluesky profile lookup."""
        mock.get(BSKY_PUBLIC_PROFILE_URL_DEFAULT, json=ATPROTO_PROFILE)
        client = AtProtoOAuthClient(self.source, self.get_request(), callback="/callback/")
        profile = client.get_profile_info({"sub": ATPROTO_DID})
        self.assertEqual(profile["did"], ATPROTO_DID)
        self.assertEqual(profile["handle"], "bsky.app")

    @Mocker()
    def test_profile_info_with_transition_email(self, mock: Mocker):
        """Test private session email lookup when transition:email is granted."""
        mock.get(BSKY_PUBLIC_PROFILE_URL_DEFAULT, json=ATPROTO_PROFILE)
        mock.get(
            f"{ATPROTO_PDS}/xrpc/com.atproto.server.getSession",
            json={"email": "user@example.com", "emailConfirmed": True},
            headers={"DPoP-Nonce": "nonce-3"},
        )
        request = self.get_request()
        request.session = {
            "authentik/sources/oauth/atproto/test": {
                "state": "state",
                "code_verifier": "verifier",
                "issuer": "https://bsky.social",
                "private_key": private_key_pem(),
                "dpop_nonce": "nonce-2",
                "login_hint": None,
                "expected_did": None,
            }
        }
        client = AtProtoOAuthClient(self.source, request, callback="/callback/")
        profile = client.get_profile_info(
            {
                "sub": ATPROTO_DID,
                "scope": "atproto transition:email",
                "access_token": "access",
                "pds_url": ATPROTO_PDS,
            }
        )
        self.assertEqual(profile["email"], "user@example.com")
        session_request = mock.request_history[1]
        self.assertEqual(session_request.headers["Authorization"], "DPoP access")
        payload = decode(session_request.headers["DPoP"], options={"verify_signature": False})
        self.assertIn("ath", payload)
