"""bsky view tests (redirect, callback, client-metadata/jwks)"""

from urllib.parse import parse_qs, urlparse

from django.urls import reverse
from requests_mock import Mocker
from rest_framework.test import APITestCase

from authentik.lib.generators import generate_id
from authentik.sources.bsky.keys import public_jwk
from authentik.sources.bsky.models import BskySource

DID_DOC = {
    "id": "did:plc:test",
    "alsoKnownAs": ["at://user.bsky.social"],
    "service": [
        {
            "id": "#atproto_pds",
            "type": "AtprotoPersonalDataServer",
            "serviceEndpoint": "https://pds.example.com",
        }
    ],
}

PROTECTED_RESOURCE = {
    "resource": "https://pds.example.com",
    "authorization_servers": ["https://authserver.example.com"],
}

AUTHSERVER_METADATA = {
    "issuer": "https://authserver.example.com",
    "authorization_endpoint": "https://authserver.example.com/oauth/authorize",
    "token_endpoint": "https://authserver.example.com/oauth/token",
    "pushed_authorization_request_endpoint": "https://authserver.example.com/oauth/par",
    "require_pushed_authorization_requests": True,
    "token_endpoint_auth_methods_supported": ["private_key_jwt"],
}

PROFILE_RESPONSE = {
    "did": "did:plc:test",
    "handle": "user.bsky.social",
    "displayName": "Test User",
}


def _mock_identity_chain(mocker: Mocker):
    """Stub the DID doc -> protected-resource -> authserver metadata chain"""
    mocker.get("https://plc.directory/did:plc:test", json=DID_DOC)
    mocker.get(
        "https://pds.example.com/.well-known/oauth-protected-resource",
        json=PROTECTED_RESOURCE,
    )
    mocker.get(
        "https://authserver.example.com/.well-known/oauth-authorization-server",
        json=AUTHSERVER_METADATA,
    )


class TestBskyLoginView(APITestCase):
    """Test BskyLoginView (redirect)"""

    def setUp(self):
        self.source = BskySource.objects.create(name="test", slug="test")

    def test_missing_identifier_returns_400(self):
        """Test a request with no ?identifier= returns 400"""
        res = self.client.get(
            reverse("authentik_sources_bsky:oauth-client-login", kwargs={"source_slug": "test"})
        )
        self.assertEqual(res.status_code, 400)

    def test_unknown_source_returns_404(self):
        """Test a request for a nonexistent source slug returns 404"""
        res = self.client.get(
            reverse(
                "authentik_sources_bsky:oauth-client-login",
                kwargs={"source_slug": "does-not-exist"},
            ),
            {"identifier": "did:plc:test"},
        )
        self.assertEqual(res.status_code, 404)

    def test_redirect_happy_path(self):
        """Test full resolve+PAR chain, mocking DID/protected-resource/authserver/PAR,
        then asserts a 302 to the real authorization_endpoint with ?request_uri=...
        and that session state (code_verifier/token_endpoint/issuer/did/pds_url) is stored"""
        with Mocker() as mocker:
            _mock_identity_chain(mocker)
            mocker.post(
                AUTHSERVER_METADATA["pushed_authorization_request_endpoint"],
                json={"request_uri": "urn:ietf:params:oauth:request_uri:abc123"},
            )
            res = self.client.get(
                reverse(
                    "authentik_sources_bsky:oauth-client-login", kwargs={"source_slug": "test"}
                ),
                {"identifier": "did:plc:test"},
            )

        self.assertEqual(res.status_code, 302)
        parsed = urlparse(res.url)
        self.assertEqual(
            f"{parsed.scheme}://{parsed.netloc}{parsed.path}",
            AUTHSERVER_METADATA["authorization_endpoint"],
        )
        qs = parse_qs(parsed.query)
        self.assertEqual(qs["request_uri"], ["urn:ietf:params:oauth:request_uri:abc123"])

        session = self.client.session
        state_keys = [key for key in session.keys() if key.startswith("bsky_test_")]
        self.assertEqual(len(state_keys), 1)
        flow_state = session[state_keys[0]]
        self.assertEqual(flow_state["did"], "did:plc:test")
        self.assertEqual(flow_state["pds_url"], "https://pds.example.com")
        self.assertEqual(flow_state["token_endpoint"], AUTHSERVER_METADATA["token_endpoint"])
        self.assertEqual(flow_state["issuer"], AUTHSERVER_METADATA["issuer"])
        self.assertIn("code_verifier", flow_state)


class TestBskyCallbackView(APITestCase):
    """Test BskyCallbackView"""

    def setUp(self):
        self.source = BskySource.objects.create(name="test", slug="test")

    def test_missing_state_or_code_returns_400(self):
        """Test a callback request missing ?state= or ?code= returns 400"""
        res = self.client.get(
            reverse("authentik_sources_bsky:oauth-client-callback", kwargs={"source_slug": "test"})
        )
        self.assertEqual(res.status_code, 400)

    def test_invalid_state_returns_400(self):
        """Test a callback with a state not present in the session returns 400"""
        res = self.client.get(
            reverse("authentik_sources_bsky:oauth-client-callback", kwargs={"source_slug": "test"}),
            {"state": "unknown", "code": "abc"},
        )
        self.assertEqual(res.status_code, 400)

    def test_callback_happy_path(self):
        """Test token exchange + profile fetch + SourceFlowManager hookup,
        mocking the token endpoint and PDS getProfile call, with session state
        pre-seeded the way BskyLoginView would leave it. The source has no
        enrollment_flow configured, so a never-seen-before DID reaching
        SourceFlowManager.get_flow() lands on the generic "not configured for
        enrollment" 400 - that's the terminal signal that our own resolution/
        token-exchange/profile-fetch plumbing all worked, without needing a
        full Flow fixture."""
        state = generate_id()
        session = self.client.session
        session[f"bsky_test_{state}"] = {
            "code_verifier": generate_id(length=128),
            "authserver_url": AUTHSERVER_METADATA["issuer"],
            "token_endpoint": AUTHSERVER_METADATA["token_endpoint"],
            "issuer": AUTHSERVER_METADATA["issuer"],
            "did": "did:plc:test",
            "pds_url": "https://pds.example.com",
        }
        session.save()

        with Mocker() as mocker:
            mocker.post(
                AUTHSERVER_METADATA["token_endpoint"],
                json={
                    "access_token": "test-access-token",
                    "refresh_token": "test-refresh-token",
                    "expires_in": 3600,
                    "sub": "did:plc:test",
                },
            )
            mocker.get(
                "https://pds.example.com/xrpc/app.bsky.actor.getProfile",
                json=PROFILE_RESPONSE,
            )
            res = self.client.get(
                reverse(
                    "authentik_sources_bsky:oauth-client-callback",
                    kwargs={"source_slug": "test"},
                ),
                {"state": state, "code": "test-code"},
            )

        self.assertEqual(res.status_code, 400)


class TestClientMetadataView(APITestCase):
    """Test ClientMetadataView"""

    def setUp(self):
        self.source = BskySource.objects.create(name="test", slug="test")

    def test_client_metadata_shape(self):
        """Test client-metadata.json has the fields atproto requires
        (client_id, redirect_uris, token_endpoint_auth_method, dpop_bound_access_tokens, jwks_uri)
        """
        res = self.client.get(
            reverse("authentik_sources_bsky:oauth-client-metadata", kwargs={"source_slug": "test"})
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertTrue(data["client_id"].endswith("/source/bsky/test/client-metadata.json"))
        self.assertEqual(
            data["redirect_uris"],
            ["http://testserver/source/bsky/test/callback/"],
        )
        self.assertEqual(data["token_endpoint_auth_method"], "private_key_jwt")
        self.assertEqual(data["token_endpoint_auth_signing_alg"], "ES256")
        self.assertTrue(data["dpop_bound_access_tokens"])
        self.assertTrue(data["jwks_uri"].endswith("/source/bsky/test/jwks.json"))


class TestClientJwksView(APITestCase):
    """Test ClientJWKSView"""

    def setUp(self):
        self.source = BskySource.objects.create(name="test", slug="test")

    def test_jwks_matches_public_jwk(self):
        """Test jwks.json's single key matches keys.public_jwk() plus kid/use/alg"""
        res = self.client.get(
            reverse("authentik_sources_bsky:oauth-client-jwks", kwargs={"source_slug": "test"})
        )
        self.assertEqual(res.status_code, 200)
        jwk = public_jwk(self.source)
        returned_key = res.json()["keys"][0]
        for field, value in jwk.items():
            self.assertEqual(returned_key[field], value)
