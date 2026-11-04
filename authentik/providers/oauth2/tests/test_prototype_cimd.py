"""PROTOTYPE (01b), never merge: smoke test the CIMD prototype path"""

from tempfile import NamedTemporaryFile

from django.test import Client, RequestFactory
from django.urls import reverse
from django.utils import timezone
from requests_mock import Mocker

from authentik.common.oauth.constants import GRANT_TYPE_AUTHORIZATION_CODE, PKCE_METHOD_S256
from authentik.core.models import Application
from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.lib.config import CONFIG
from authentik.lib.generators import generate_id
from authentik.providers.oauth2.errors import RedirectUriError
from authentik.providers.oauth2.models import (
    AccessToken,
    AuthorizationCode,
    ClientType,
    GrantType,
    OAuth2Provider,
)
from authentik.providers.oauth2.prototype_cimd import METADATA_KIND, _cache, scoped_resolver
from authentik.providers.oauth2.tests.utils import OAuthTestCase
from authentik.providers.oauth2.utils import pkce_s256_challenge
from authentik.providers.oauth2.views.authorize import OAuthAuthorizationParams

CLIENT_ID = "https://client.invalid/oauth/metadata.json"
DOCUMENT = {
    "client_id": CLIENT_ID,
    "client_name": "Test MCP client",
    "redirect_uris": ["http://127.0.0.1:33418/callback"],
    "grant_types": ["authorization_code", "refresh_token"],
    "response_types": ["code"],
    "token_endpoint_auth_method": "none",
}


class TestPrototypeCIMD(OAuthTestCase):
    def setUp(self) -> None:
        super().setUp()
        _cache.clear()
        self.slug = generate_id()
        self.provider = OAuth2Provider.objects.create(
            name=generate_id(),
            client_type=ClientType.PUBLIC,
            authorization_flow=create_test_flow(),
            grant_types=[GrantType.AUTHORIZATION_CODE, GrantType.REFRESH_TOKEN],
            redirect_uris=[],
            signing_key=self.keypair,
        )
        Application.objects.create(name=generate_id(), slug=self.slug, provider=self.provider)
        self.log = NamedTemporaryFile(suffix=".jsonl")
        self.patches = [
            CONFIG.patch("cimd_prototype.applications", self.slug),
            CONFIG.patch("cimd_prototype.log", self.log.name),
        ]
        for patch in self.patches:
            patch.__enter__()

    def tearDown(self) -> None:
        for patch in reversed(self.patches):
            patch.__exit__(None, None, None)
        self.log.close()
        super().tearDown()

    def test_discovery(self):
        response = self.client.get(
            reverse(
                "authentik_providers_oauth2_root:providers-oauth2-authorization-server-metadata",
                kwargs={"application_slug": self.slug},
            )
        )
        body = response.json()
        self.assertTrue(body["client_id_metadata_document_supported"])
        self.assertTrue(body["authorization_endpoint"].endswith(f"/{self.slug}/authorize/"))
        self.assertTrue(body["token_endpoint"].endswith(f"/{self.slug}/token/"))

    @Mocker()
    def test_authorize_loopback_port(self, mock: Mocker):
        mock.get(CLIENT_ID, json=DOCUMENT)
        request = RequestFactory().get(
            "/",
            data={
                "response_type": "code",
                "client_id": CLIENT_ID,
                "redirect_uri": "http://127.0.0.1:51234/callback",
                "code_challenge": "x" * 43,
                "code_challenge_method": PKCE_METHOD_S256,
            },
        )
        params = OAuthAuthorizationParams.from_request(
            request, resolver=scoped_resolver(self.provider)
        )
        self.assertEqual(params.client.registration_kind, METADATA_KIND)
        self.assertEqual(params.provider, self.provider)
        # Wrong path is rejected
        request = RequestFactory().get(
            "/",
            data={
                "response_type": "code",
                "client_id": CLIENT_ID,
                "redirect_uri": "http://127.0.0.1:51234/other",
            },
        )
        with self.assertRaises(RedirectUriError):
            OAuthAuthorizationParams.from_request(request, resolver=scoped_resolver(self.provider))

    @Mocker()
    def test_token(self, mock: Mocker):
        mock.get(CLIENT_ID, json=DOCUMENT)
        verifier = generate_id(64)
        code = AuthorizationCode.objects.create(
            code=generate_id(),
            provider=self.provider,
            user=create_test_admin_user(),
            auth_time=timezone.now(),
            code_challenge=pkce_s256_challenge(verifier),
            code_challenge_method=PKCE_METHOD_S256,
        )
        # Real clients send no CSRF token
        response = Client(enforce_csrf_checks=True).post(
            reverse(
                "authentik_providers_oauth2:prototype-scoped-token",
                kwargs={"application_slug": self.slug},
            ),
            data={
                "grant_type": GRANT_TYPE_AUTHORIZATION_CODE,
                "client_id": CLIENT_ID,
                "code": code.code,
                "code_verifier": verifier,
                "redirect_uri": "http://127.0.0.1:51234/callback",
            },
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertTrue(AccessToken.objects.filter(provider=self.provider).exists())
        with open(self.log.name) as log:
            self.assertIn('"kind": "metadata_fetch"', log.read())

    def test_disabled_slug_404(self):
        Application.objects.create(
            name=generate_id(),
            slug="other",
            provider=OAuth2Provider.objects.create(
                name=generate_id(), authorization_flow=create_test_flow()
            ),
        )
        response = self.client.post(
            reverse(
                "authentik_providers_oauth2:prototype-scoped-token",
                kwargs={"application_slug": "other"},
            ),
            data={"grant_type": GRANT_TYPE_AUTHORIZATION_CODE, "client_id": CLIENT_ID},
        )
        self.assertEqual(response.status_code, 404)
