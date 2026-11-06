"""Test OAuth client resolution: provider selectors, client adapters and resolvers"""

from base64 import b64encode
from dataclasses import FrozenInstanceError, dataclass, make_dataclass, replace
from pickle import dumps, loads  # nosec
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

from django.test import RequestFactory
from django.urls import reverse

from authentik.blueprints.tests import apply_blueprint
from authentik.common.oauth.constants import GRANT_TYPE_CLIENT_CREDENTIALS, SCOPE_OPENID
from authentik.core.models import Application
from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.flows.models import FlowToken
from authentik.flows.planner import FlowPlan
from authentik.flows.views.executor import FlowExecutorView
from authentik.lib.generators import generate_id
from authentik.providers.oauth2.client import (
    ClientAdapter,
    ClientRegistrationKind,
    LegacyClientAdapter,
    LegacyProviderSelector,
    OAuthClientContext,
    OAuthClientResolver,
    ProviderSelector,
)
from authentik.providers.oauth2.models import (
    AccessToken,
    AuthorizationCode,
    ClientType,
    GrantType,
    OAuth2Provider,
    RedirectURI,
    RedirectURIMatchingMode,
    RedirectURIType,
    ResponseMode,
    ScopeMapping,
)
from authentik.providers.oauth2.tests.utils import OAuthTestCase
from authentik.providers.oauth2.token.authorization_code import AuthorizationCodeTokenRequest
from authentik.providers.oauth2.token.router import parse_token_request
from authentik.providers.oauth2.utils import authenticate_client, client_from_request
from authentik.providers.oauth2.views.authorize import (
    PLAN_CONTEXT_PARAMS,
    OAuthAuthorizationParams,
    OAuthFulfillmentStage,
)

HTTPS_CLIENT_ID = "https://client.example.com/oauth/client-metadata.json"


@dataclass(frozen=True, slots=True)
class ExtendedClientContext(OAuthClientContext):
    """Context for a registration kind defined outside core"""

    client_name: str = ""


class FixedSelector(ProviderSelector):
    """Selector which always selects the same provider"""

    def __init__(self, provider: OAuth2Provider | None):
        self.provider = provider

    def select(self, request, client_id):
        return self.provider


class TestClientContext(OAuthTestCase):
    """Test OAuth client context and resolution"""

    def setUp(self) -> None:
        super().setUp()
        self.factory = RequestFactory()
        self.provider = OAuth2Provider.objects.create(
            name=generate_id(),
            authorization_flow=create_test_flow(),
            grant_types=[GrantType.AUTHORIZATION_CODE, GrantType.REFRESH_TOKEN],
            redirect_uris=[
                RedirectURI(RedirectURIMatchingMode.STRICT, "http://local.invalid/callback"),
                RedirectURI(
                    RedirectURIMatchingMode.STRICT,
                    "http://local.invalid/logout",
                    RedirectURIType.LOGOUT,
                ),
            ],
            signing_key=self.keypair,
        )
        self.app = Application.objects.create(
            name=generate_id(), slug=generate_id(), provider=self.provider
        )

    def test_legacy_context(self):
        """Legacy context mirrors the registered provider"""
        client = OAuthClientContext.for_provider(self.provider)
        self.assertEqual(client.provider, self.provider)
        self.assertEqual(client.application, self.app)
        self.assertEqual(client.client_id, self.provider.client_id)
        self.assertEqual(client.registration_kind, ClientRegistrationKind.LEGACY)
        self.assertTrue(client.is_legacy)
        self.assertTrue(client.is_confidential)
        self.assertEqual(
            client.grant_types,
            frozenset([GrantType.AUTHORIZATION_CODE, GrantType.REFRESH_TOKEN]),
        )
        # Only authorization redirect URIs are valid redirect targets
        self.assertEqual(
            client.redirect_uris,
            (RedirectURI(RedirectURIMatchingMode.STRICT, "http://local.invalid/callback"),),
        )

    def test_legacy_context_public(self):
        """Public legacy clients are not confidential"""
        self.provider.client_type = ClientType.PUBLIC
        self.provider.save()
        client = OAuthClientContext.for_provider(self.provider)
        self.assertFalse(client.is_confidential)

    def test_context_without_application(self):
        """Application is None when the provider is not assigned"""
        self.app.provider = None
        self.app.save()
        provider = OAuth2Provider.objects.get(pk=self.provider.pk)
        self.assertIsNone(OAuthClientContext.for_provider(provider).application)

    def test_context_immutable(self):
        """Context cannot be modified"""
        client = OAuthClientContext.for_provider(self.provider)
        with self.assertRaises(FrozenInstanceError):
            client.client_id = "foo"  # type: ignore[misc]

    def test_context_pickle(self):
        """Context survives being pickled into a flow plan"""
        client = OAuthClientContext.for_provider(OAuth2Provider.objects.get(pk=self.provider.pk))
        restored = loads(dumps(client))  # nosec
        self.assertEqual(restored, client)
        self.assertEqual(restored.provider.pk, self.provider.pk)

    def test_legacy_authorization_params_pickle_fulfillment(self):
        """Pre-client slotted pickles resume code and hybrid fulfillment after an upgrade."""
        request = self.factory.get("/")
        request.user = create_test_admin_user()
        request.session = {"authenticatedsession": None}
        for grant_type, response_type, response_mode in (
            (GrantType.AUTHORIZATION_CODE, "code", ResponseMode.QUERY),
            (GrantType.HYBRID, "code id_token token", ResponseMode.FRAGMENT),
        ):
            with self.subTest(grant_type=grant_type):
                legacy_values = {
                    "client_id": self.provider.client_id,
                    "redirect_uri": "http://local.invalid/callback",
                    "response_type": response_type,
                    "response_mode": response_mode,
                    "scope": {SCOPE_OPENID},
                    "state": "saved-state",
                    "nonce": "saved-nonce",
                    "prompt": set(),
                    "grant_type": grant_type,
                    "provider": OAuth2Provider.objects.get(pk=self.provider.pk),
                    "request": None,
                    "max_age": None,
                    "code_challenge": None,
                    "code_challenge_method": None,
                    "dpop_jkt": None,
                }
                legacy_class = make_dataclass(
                    "OAuthAuthorizationParams",
                    legacy_values,
                    slots=True,
                    module=OAuthAuthorizationParams.__module__,
                )
                with patch(
                    "authentik.providers.oauth2.views.authorize.OAuthAuthorizationParams",
                    legacy_class,
                ):
                    plan = FlowPlan(
                        flow_pk=self.provider.authorization_flow_id.hex,
                        context={PLAN_CONTEXT_PARAMS: legacy_class(**legacy_values)},
                    )
                    saved_flow = FlowToken.objects.create(
                        user=request.user,
                        identifier=generate_id(),
                        flow_id=self.provider.authorization_flow_id,
                        _plan=FlowToken.pickle(plan),
                    )
                restored = FlowToken.objects.get(pk=saved_flow.pk).plan.context[PLAN_CONTEXT_PARAMS]
                self.assertIsInstance(restored, OAuthAuthorizationParams)
                self.assertFalse(hasattr(restored, "client"))
                stage = OAuthFulfillmentStage(FlowExecutorView())
                stage.request = request
                stage.provider = self.provider
                stage.params = restored
                uri = urlsplit(stage.create_response_uri())
                response = parse_qs(
                    uri.query if response_mode == ResponseMode.QUERY else uri.fragment
                )
                self.assertEqual(response["state"], ["saved-state"])
                code = AuthorizationCode.objects.get(code=response["code"][0])
                registered = OAuthClientContext.for_provider(self.provider)
                self.assertTrue(code.is_bound_to(registered))
                self.assertEqual(code.client_id, self.provider.client_id)
                self.assertEqual(code.nonce, "saved-nonce")
                self.assertEqual(code.redirect_uri, legacy_values["redirect_uri"])
                if grant_type == GrantType.HYBRID:
                    token = AccessToken.objects.get(token=response["access_token"][0])
                    self.assertTrue(token.is_bound_to(registered))
                    self.assertEqual(token.client_id, self.provider.client_id)
                    self.assertEqual(token.id_token.aud, self.provider.client_id)

    def test_check_client_secret(self):
        """Shared secrets are checked against the registered provider"""
        client = OAuthClientContext.for_provider(self.provider)
        self.assertTrue(client.check_client_secret(self.provider.client_secret))
        self.assertFalse(client.check_client_secret(self.provider.client_secret + "a"))
        self.assertFalse(client.check_client_secret(""))

    def test_legacy_adapter(self):
        """Legacy adapter only resolves the provider's own client_id"""
        adapter = LegacyClientAdapter()
        client = adapter.resolve(None, self.provider, self.provider.client_id)
        self.assertIsNotNone(client)
        self.assertEqual(client.provider, self.provider)
        self.assertIsNone(adapter.resolve(None, self.provider, generate_id()))
        # Exact match only
        self.assertIsNone(adapter.resolve(None, self.provider, self.provider.client_id.upper()))
        self.assertIsNone(adapter.resolve(None, self.provider, f" {self.provider.client_id}"))

    def test_legacy_selector(self):
        """Legacy selector finds providers by registered client_id"""
        selector = LegacyProviderSelector()
        self.assertEqual(selector.select(None, self.provider.client_id), self.provider)
        self.assertIsNone(selector.select(None, generate_id()))
        self.assertIsNone(selector.select(None, ""))

    def test_resolver(self):
        """Legacy resolver resolves registered clients and nothing else"""
        resolver = OAuthClientResolver.legacy()
        client = resolver.resolve(None, self.provider.client_id)
        self.assertEqual(client, OAuthClientContext.for_provider(self.provider))
        self.assertIsNone(resolver.resolve(None, generate_id()))
        self.assertIsNone(resolver.resolve(None, ""))

    def test_resolver_adapter_order(self):
        """Adapters are consulted in order, first match wins"""
        calls = []

        class NeverAdapter(ClientAdapter):
            def resolve(self, request, provider, client_id):
                calls.append("never")

        class AlwaysAdapter(ClientAdapter):
            def resolve(self, request, provider, client_id):
                calls.append("always")
                return ExtendedClientContext(
                    provider=provider,
                    client_id=client_id,
                    registration_kind="extended",
                    client_type=ClientType.PUBLIC,
                    redirect_uris=(),
                    grant_types=frozenset([GrantType.AUTHORIZATION_CODE]),
                    client_name="test",
                )

        resolver = OAuthClientResolver(
            LegacyProviderSelector(),
            [LegacyClientAdapter(), NeverAdapter(), AlwaysAdapter()],
        )
        # Registered client wins, later adapters are not consulted
        client = resolver.resolve(None, self.provider.client_id)
        self.assertTrue(client.is_legacy)
        self.assertEqual(calls, [])

        # Otherwise adapters are tried in order within the selected provider
        resolver = OAuthClientResolver(
            FixedSelector(self.provider),
            [LegacyClientAdapter(), NeverAdapter(), AlwaysAdapter()],
        )
        client = resolver.resolve(None, HTTPS_CLIENT_ID)
        self.assertIsInstance(client, ExtendedClientContext)
        self.assertEqual(client.registration_kind, "extended")
        self.assertFalse(client.is_legacy)
        # Clients of other kinds never authenticate with the provider's shared secret
        self.assertFalse(client.check_client_secret(self.provider.client_secret))
        self.assertEqual(client.provider, self.provider)
        self.assertEqual(calls, ["never", "always"])
        # Extended contexts are stored in flow plans too
        client = replace(client, provider=OAuth2Provider.objects.get(pk=self.provider.pk))
        self.assertEqual(loads(dumps(client)), client)  # nosec

    def test_resolver_selector(self):
        """A selector decides the provider; adapters resolve the client within it"""
        other = OAuth2Provider.objects.create(
            name=generate_id(), authorization_flow=create_test_flow()
        )
        # The selected provider does not have this client registered
        resolver = OAuthClientResolver(FixedSelector(other))
        self.assertIsNone(resolver.resolve(None, self.provider.client_id))
        # Nothing selected
        self.assertIsNone(OAuthClientResolver(FixedSelector(None)).resolve(None, "foo"))

    def test_client_from_request(self):
        """Credential helpers resolve a client context"""
        request = self.factory.post(
            "/",
            data={
                "client_id": self.provider.client_id,
                "client_secret": self.provider.client_secret,
            },
        )
        client, client_id, client_secret = client_from_request(request)
        self.assertEqual(client.provider, self.provider)
        self.assertEqual(client_id, self.provider.client_id)
        self.assertEqual(client_secret, self.provider.client_secret)
        self.assertEqual(authenticate_client(request), client)

        # No credentials at all
        self.assertEqual(client_from_request(self.factory.post("/")), (None, "", ""))

    def test_authenticate_client_wrong_secret(self):
        """Wrong secret does not authenticate"""
        header = b64encode(f"{self.provider.client_id}:wrong".encode()).decode()
        request = self.factory.post("/", HTTP_AUTHORIZATION=f"Basic {header}")
        client, _, _ = client_from_request(request)
        self.assertIsNotNone(client)
        self.assertIsNone(authenticate_client(request))

    def test_parse_token_request_client(self):
        """Grant router passes the resolved client to the token request"""
        request = self.factory.post(
            "/",
            data={
                "grant_type": "authorization_code",
                "code": "foo",
                "redirect_uri": "http://local.invalid/callback",
            },
        )
        client = OAuthClientContext.for_provider(self.provider)
        with patch.object(AuthorizationCodeTokenRequest, "parse") as parse:
            params = parse_token_request(request, client, self.provider.client_secret)
        parse.assert_called_once()
        self.assertIs(params.client, client)
        self.assertEqual(params.provider, self.provider)
        self.assertEqual(params.client_id, self.provider.client_id)

    def test_authorize_params_client(self):
        """Authorization params carry the resolved client"""
        request = self.factory.get(
            "/",
            data={
                "response_type": "code",
                "client_id": self.provider.client_id,
                "redirect_uri": "http://local.invalid/callback",
            },
        )
        params = OAuthAuthorizationParams.from_request(request)
        self.assertEqual(params.client, OAuthClientContext.for_provider(self.provider))
        self.assertEqual(params.provider, self.provider)
        restored = loads(dumps(params))  # nosec
        self.assertEqual(restored.client, params.client)


class TestHTTPSStaticClient(OAuthTestCase):
    """A registered client_id shaped like a URL stays a static client"""

    @apply_blueprint("system/providers-oauth2.yaml")
    def setUp(self) -> None:
        super().setUp()
        self.factory = RequestFactory()
        self.provider = OAuth2Provider.objects.create(
            name=generate_id(),
            client_id=HTTPS_CLIENT_ID,
            authorization_flow=create_test_flow(),
            grant_types=[GrantType.AUTHORIZATION_CODE, GrantType.CLIENT_CREDENTIALS],
            redirect_uris=[
                RedirectURI(RedirectURIMatchingMode.STRICT, "http://local.invalid/callback")
            ],
            signing_key=self.keypair,
        )
        self.provider.property_mappings.set(ScopeMapping.objects.all())
        self.app = Application.objects.create(
            name=generate_id(), slug=generate_id(), provider=self.provider
        )

    def test_resolve(self):
        """Resolution returns the legacy client without any network access"""
        with (
            patch("requests.sessions.Session.send") as send,
            patch("urllib3.connectionpool.HTTPConnectionPool.urlopen") as urlopen,
        ):
            client = OAuthClientResolver.legacy().resolve(None, HTTPS_CLIENT_ID)
            # Unregistered URL-valued IDs are not resolved and not fetched
            self.assertIsNone(
                OAuthClientResolver.legacy().resolve(None, "https://other.example.com/client")
            )
        send.assert_not_called()
        urlopen.assert_not_called()
        self.assertEqual(client.registration_kind, ClientRegistrationKind.LEGACY)
        self.assertEqual(client.client_id, HTTPS_CLIENT_ID)
        self.assertEqual(client.provider, self.provider)

    def test_authorize(self):
        """Authorization request resolves the static client"""
        request = self.factory.get(
            "/",
            data={
                "response_type": "code",
                "client_id": HTTPS_CLIENT_ID,
                "redirect_uri": "http://local.invalid/callback",
                "scope": SCOPE_OPENID,
            },
        )
        with patch("requests.sessions.Session.send") as send:
            params = OAuthAuthorizationParams.from_request(request)
        send.assert_not_called()
        self.assertTrue(params.client.is_legacy)
        self.assertEqual(params.provider, self.provider)

    def test_token(self):
        """Token endpoint authenticates the static client by its secret"""
        with patch("requests.sessions.Session.send") as send:
            response = self.client.post(
                reverse("authentik_providers_oauth2:token"),
                {
                    "grant_type": GRANT_TYPE_CLIENT_CREDENTIALS,
                    "scope": SCOPE_OPENID,
                    "client_id": HTTPS_CLIENT_ID,
                    "client_secret": self.provider.client_secret,
                },
            )
        send.assert_not_called()
        self.assertEqual(response.status_code, 200)
        self.assertIn("access_token", response.json())
