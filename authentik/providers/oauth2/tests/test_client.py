"""Test OAuth client context resolution"""

from dataclasses import FrozenInstanceError

from django.test import RequestFactory
from django.urls import reverse
from django.utils import timezone
from requests_mock import Mocker

from authentik.common.oauth.constants import GRANT_TYPE_AUTHORIZATION_CODE
from authentik.core.models import Application
from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.lib.generators import generate_id
from authentik.providers.oauth2.client import (
    ClientRegistrationKind,
    LegacyClientSelector,
    OAuthClientContext,
)
from authentik.providers.oauth2.errors import ClientIdError
from authentik.providers.oauth2.models import (
    AccessToken,
    AuthorizationCode,
    ClientType,
    GrantType,
    OAuth2Provider,
    RedirectURI,
    RedirectURIMatchingMode,
)
from authentik.providers.oauth2.tests.utils import OAuthTestCase
from authentik.providers.oauth2.views.authorize import OAuthAuthorizationParams

URL_CLIENT_ID = "https://client.invalid/oauth-client.json"
REDIRECT_URI = "http://local.invalid/callback"


class TestClientContext(OAuthTestCase):
    """Test OAuth client context resolution"""

    def setUp(self) -> None:
        super().setUp()
        self.factory = RequestFactory()

    def create_provider(self, client_id: str) -> OAuth2Provider:
        provider = OAuth2Provider.objects.create(
            name=generate_id(),
            client_id=client_id,
            client_type=ClientType.PUBLIC,
            authorization_flow=create_test_flow(),
            grant_types=[GrantType.AUTHORIZATION_CODE],
            redirect_uris=[RedirectURI(RedirectURIMatchingMode.STRICT, REDIRECT_URI)],
            signing_key=self.keypair,
        )
        Application.objects.create(name=generate_id(), slug=generate_id(), provider=provider)
        return provider

    def test_legacy_resolve(self):
        """Registered clients resolve to their provider"""
        provider = self.create_provider(generate_id())
        client = LegacyClientSelector().resolve(provider.client_id)
        self.assertEqual(client, OAuthClientContext.for_provider(provider))
        self.assertEqual(client.provider, provider)
        self.assertEqual(client.client_id, provider.client_id)
        self.assertEqual(client.registration_kind, ClientRegistrationKind.LEGACY)
        with self.assertRaises(FrozenInstanceError):
            client.client_id = generate_id()

    def test_legacy_resolve_unknown(self):
        """Unknown and inexact client IDs do not resolve"""
        provider = self.create_provider(generate_id())
        selector = LegacyClientSelector()
        self.assertIsNone(selector.resolve(generate_id()))
        self.assertIsNone(selector.resolve(""))
        self.assertIsNone(selector.resolve(provider.client_id.upper()))

    @Mocker()
    def test_url_client_id_authorize(self, mock: Mocker):
        """A registered HTTPS client ID is a static client, and nothing is fetched"""
        provider = self.create_provider(URL_CLIENT_ID)
        request = self.factory.get(
            "/",
            data={
                "response_type": "code",
                "client_id": URL_CLIENT_ID,
                "redirect_uri": REDIRECT_URI,
            },
        )
        params = OAuthAuthorizationParams.from_request(request)
        self.assertEqual(params.provider, provider)
        self.assertEqual(params.client, OAuthClientContext.for_provider(provider))
        self.assertFalse(mock.called)

    @Mocker()
    def test_url_client_id_authorize_unknown(self, mock: Mocker):
        """An unregistered HTTPS client ID is rejected without fetching it"""
        self.create_provider(generate_id())
        request = self.factory.get(
            "/",
            data={
                "response_type": "code",
                "client_id": URL_CLIENT_ID,
                "redirect_uri": REDIRECT_URI,
            },
        )
        with self.assertRaises(ClientIdError):
            OAuthAuthorizationParams.from_request(request)
        self.assertFalse(mock.called)

    @Mocker()
    def test_url_client_id_flow_init(self, mock: Mocker):
        """The flow init view resolves a registered HTTPS client ID"""
        self.create_provider(URL_CLIENT_ID)
        self.client.force_login(create_test_admin_user())
        data = {
            "response_type": "code",
            "redirect_uri": REDIRECT_URI,
        }
        response = self.client.get(
            reverse("authentik_providers_oauth2:authorize"),
            data={**data, "client_id": URL_CLIENT_ID},
        )
        self.assertEqual(response.status_code, 302)
        response = self.client.get(
            reverse("authentik_providers_oauth2:authorize"),
            data={**data, "client_id": "https://client.invalid/unknown.json"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(mock.called)

    @Mocker()
    def test_url_client_id_token(self, mock: Mocker):
        """A registered HTTPS client ID can redeem a code, and nothing is fetched"""
        provider = self.create_provider(URL_CLIENT_ID)
        user = create_test_admin_user()
        code = AuthorizationCode.objects.create(
            code=generate_id(), provider=provider, user=user, auth_time=timezone.now()
        )
        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            data={
                "grant_type": GRANT_TYPE_AUTHORIZATION_CODE,
                "client_id": URL_CLIENT_ID,
                "code": code.code,
                "redirect_uri": REDIRECT_URI,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(AccessToken.objects.filter(provider=provider, user=user).exists())
        self.assertFalse(mock.called)

    @Mocker()
    def test_url_client_id_token_unknown(self, mock: Mocker):
        """An unregistered HTTPS client ID is rejected at the token endpoint"""
        self.create_provider(generate_id())
        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            data={
                "grant_type": GRANT_TYPE_AUTHORIZATION_CODE,
                "client_id": URL_CLIENT_ID,
                "code": generate_id(),
                "redirect_uri": REDIRECT_URI,
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "invalid_client")
        self.assertFalse(mock.called)
