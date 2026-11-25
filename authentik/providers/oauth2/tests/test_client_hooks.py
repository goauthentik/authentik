"""Test the per-client policy hooks of OAuthClientContext, with their legacy defaults and a
test-only client of another registration kind which overrides every one of them"""

from base64 import b64encode
from dataclasses import dataclass, field, replace
from datetime import timedelta
from json import loads
from re import error as RegexError
from unittest.mock import MagicMock, patch
from urllib.parse import parse_qs, urlsplit

from django.test import RequestFactory
from django.urls import reverse
from django.utils import timezone
from jwt import decode

from authentik.blueprints.tests import apply_blueprint
from authentik.common.oauth.constants import (
    GRANT_TYPE_AUTHORIZATION_CODE,
    GRANT_TYPE_REFRESH_TOKEN,
    PKCE_METHOD_PLAIN,
    PKCE_METHOD_S256,
    SCOPE_GITHUB_USER_EMAIL,
    SCOPE_OFFLINE_ACCESS,
    SCOPE_OPENID,
)
from authentik.core.models import Application
from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.flows.models import Flow, FlowStageBinding
from authentik.flows.views.executor import SESSION_KEY_PLAN
from authentik.lib.generators import generate_id
from authentik.providers.oauth2.client import (
    ClientAdapter,
    LegacyClientAdapter,
    OAuthClientContext,
    OAuthClientResolver,
    ProviderSelector,
)
from authentik.providers.oauth2.id_token import IDToken
from authentik.providers.oauth2.models import (
    AccessToken,
    AuthorizationCode,
    ClientType,
    GrantType,
    OAuth2Provider,
    RedirectURI,
    RedirectURIMatchingMode,
    RefreshToken,
    ScopeMapping,
    join_resources,
)
from authentik.providers.oauth2.resources import ResourceIndicatorError, resolve_resources
from authentik.providers.oauth2.tests.utils import OAuthTestCase
from authentik.providers.oauth2.token.router import parse_token_request
from authentik.providers.oauth2.utils import pkce_s256_challenge
from authentik.providers.oauth2.views.authorize import (
    PLAN_CONTEXT_PARAMS,
    AuthorizationFlowInitView,
    OAuthAuthorizationParams,
)
from authentik.providers.oauth2.views.introspection import TokenIntrospectionView
from authentik.providers.oauth2.views.provider import provider_info_contributors
from authentik.providers.oauth2.views.token import TokenView
from authentik.providers.oauth2.views.token_revoke import TokenRevokeView
from authentik.stages.consent.models import ConsentMode, ConsentStage

CLIENT = "https://client.example.com/oauth/metadata.json"
# Registered for the hooked client, which accepts it on any port
REDIRECT = "http://127.0.0.1:1234/callback"
REDIRECT_OTHER_PORT = "http://127.0.0.1:50123/callback"
REDIRECT_REGISTERED = "https://app.example.com/callback"
RESOURCE_1 = "https://mcp-1.example.com/mcp"
RESOURCE_2 = "https://mcp-2.example.com/mcp"
RESOURCE_3 = "https://mcp-3.example.com/mcp"
VERIFIER = generate_id(64)


@dataclass(frozen=True, slots=True)
class HookedClientContext(OAuthClientContext):
    """Test-only client of a registration kind core does not know, which overrides every
    policy hook of the context"""

    # Slug of the flow users authorize this client with
    flow_slug: str = field(default="", kw_only=True)
    resources: frozenset[str] = field(default=frozenset(), kw_only=True)
    defaults: tuple[str, ...] = field(default=(), kw_only=True)

    def allows_redirect_uri(self, redirect_uri, on_invalid_pattern=None) -> bool:
        """Loopback redirect URIs are allowed on any port, everything else must match"""
        presented = urlsplit(redirect_uri)
        for allowed in self.redirect_uris:
            registered = urlsplit(allowed.url)
            if (
                registered.hostname == "127.0.0.1"
                and presented.scheme == registered.scheme
                and presented.hostname == registered.hostname
                and presented.path == registered.path
                and presented.query == registered.query
            ):
                return True
        return False

    @property
    def authorization_flow(self) -> Flow | None:
        return Flow.objects.get(slug=self.flow_slug)

    def allowed_resources(self) -> frozenset[str]:
        return self.resources

    def default_resources(self) -> tuple[str, ...]:
        return self.defaults

    @property
    def requires_single_resource(self) -> bool:
        return True

    def rotates_refresh_tokens(self, refresh_token, now) -> bool:
        return True


class FixedSelector(ProviderSelector):
    """Selects one provider, loaded fresh for every request"""

    def __init__(self, provider: OAuth2Provider):
        self.pk = provider.pk

    def select(self, request, client_id):
        return OAuth2Provider.objects.get(pk=self.pk)


class HookedAdapter(ClientAdapter):
    """Resolves the hooked client, built by `factory`"""

    def __init__(self, factory):
        self.factory = factory

    def resolve(self, request, provider, client_id):
        if client_id == CLIENT:
            return self.factory(provider)
        return None


class TestLegacyHookDefaults(OAuthTestCase):
    """The hooks of a registered client reproduce the provider's configuration"""

    def setUp(self) -> None:
        super().setUp()
        self.flow = create_test_flow()
        self.provider = OAuth2Provider.objects.create(
            name=generate_id(),
            authorization_flow=self.flow,
            redirect_uris=[
                RedirectURI(RedirectURIMatchingMode.STRICT, REDIRECT_REGISTERED),
                RedirectURI(RedirectURIMatchingMode.REGEX, r"https://(.*)\.example\.org/cb"),
                RedirectURI(RedirectURIMatchingMode.REGEX, "https://broken(/cb"),
            ],
            allowed_resources=[RESOURCE_1, RESOURCE_2],
        )
        self.client_context = OAuthClientContext.for_provider(self.provider)

    def test_defaults(self):
        client = self.client_context
        self.assertFalse(client.pkce_required)
        self.assertIsNone(client.pkce_methods)
        self.assertEqual(client.authorization_flow, self.flow)
        self.assertEqual(client.allowed_resources(), frozenset([RESOURCE_1, RESOURCE_2]))
        self.assertEqual(client.default_resources(), ())
        self.assertFalse(client.requires_single_resource)

    def test_allows_redirect_uri(self):
        """Strict and regular expression matching, as configured on the provider"""
        client = self.client_context
        invalid = MagicMock()
        self.assertTrue(client.allows_redirect_uri(REDIRECT_REGISTERED, invalid))
        self.assertTrue(client.allows_redirect_uri("https://foo.example.org/cb", invalid))
        self.assertFalse(client.allows_redirect_uri(REDIRECT_REGISTERED + "/", invalid))
        self.assertFalse(client.allows_redirect_uri("https://foo.example.org/cb2", invalid))
        # The broken pattern is reported every time it is tried, and never matches
        self.assertEqual(invalid.call_count, 2)
        pattern, exc = invalid.call_args.args
        self.assertEqual(pattern.url, "https://broken(/cb")
        self.assertIsInstance(exc, RegexError)
        # Without a handler, it is only logged
        self.assertFalse(client.allows_redirect_uri("https://other.example.net"))

    def test_rotates_refresh_tokens(self):
        """Refresh tokens rotate per the provider's refresh token threshold"""
        now = timezone.now()
        token = RefreshToken(provider=self.provider, expires=now + timedelta(days=10))
        self.provider.refresh_token_threshold = "seconds=0"
        self.assertTrue(self.client_context.rotates_refresh_tokens(token, now))
        self.provider.refresh_token_threshold = "days=5"
        self.assertFalse(self.client_context.rotates_refresh_tokens(token, now))
        self.provider.refresh_token_threshold = "days=30"
        self.assertTrue(self.client_context.rotates_refresh_tokens(token, now))

    def test_resolve_resources_unchanged(self):
        """Without hooks overridden, requests without resources stay unrestricted"""
        self.assertEqual(resolve_resources(self.client_context, []), ())
        self.assertEqual(
            resolve_resources(self.client_context, [RESOURCE_1, RESOURCE_2]),
            (RESOURCE_1, RESOURCE_2),
        )
        self.assertEqual(resolve_resources(self.client_context, [], (RESOURCE_2,)), (RESOURCE_2,))


class TestClientHooks(OAuthTestCase):
    """A client which overrides every hook, at every endpoint consulting them"""

    @apply_blueprint("system/providers-oauth2.yaml")
    def setUp(self) -> None:
        super().setUp()
        self.factory = RequestFactory()
        self.user = create_test_admin_user()
        # The provider's flow completes silently; the hooked client's asks for consent
        self.client_flow = create_test_flow()
        FlowStageBinding.objects.create(
            target=self.client_flow,
            stage=ConsentStage.objects.create(name=generate_id(), mode=ConsentMode.ALWAYS_REQUIRE),
            order=0,
        )
        self.provider = OAuth2Provider.objects.create(
            name=generate_id(),
            authorization_flow=create_test_flow(),
            client_type=ClientType.CONFIDENTIAL,
            grant_types=[GrantType.AUTHORIZATION_CODE, GrantType.REFRESH_TOKEN],
            redirect_uris=[RedirectURI(RedirectURIMatchingMode.STRICT, REDIRECT_REGISTERED)],
            signing_key=self.keypair,
            allowed_resources=[RESOURCE_1, RESOURCE_2, RESOURCE_3],
            # Registered clients would only rotate refresh tokens close to their expiry
            refresh_token_threshold="days=1",
        )
        self.provider.property_mappings.set(
            ScopeMapping.objects.filter(
                managed__in=[
                    "goauthentik.io/providers/oauth2/scope-openid",
                    "goauthentik.io/providers/oauth2/scope-offline_access",
                ]
            )
        )
        self.app = Application.objects.create(
            name=generate_id(), slug=generate_id(), provider=self.provider
        )
        self.hooked = self.hooked_client(self.provider)
        self.use_client(self.hooked_client)

    def hooked_client(self, provider: OAuth2Provider, **kwargs) -> HookedClientContext:
        """Public client requiring S256 PKCE and exactly one of two resources"""
        options = {
            "flow_slug": self.client_flow.slug,
            "resources": frozenset([RESOURCE_1, RESOURCE_2]),
            "defaults": (RESOURCE_1,),
            "pkce_required": True,
            "pkce_methods": frozenset([PKCE_METHOD_S256]),
        }
        options.update(kwargs)
        options.setdefault(
            "redirect_uris", (RedirectURI(RedirectURIMatchingMode.STRICT, REDIRECT),)
        )
        return HookedClientContext(
            provider=provider,
            client_id=CLIENT,
            registration_kind="hooked",
            client_type=ClientType.PUBLIC,
            grant_types=frozenset([GrantType.AUTHORIZATION_CODE, GrantType.REFRESH_TOKEN]),
            **options,
        )

    def use_client(self, factory):
        """Resolve the hooked client built by `factory` at every endpoint"""
        resolver = OAuthClientResolver(
            FixedSelector(self.provider), [LegacyClientAdapter(), HookedAdapter(factory)]
        )
        for view in (
            AuthorizationFlowInitView,
            TokenView,
            TokenRevokeView,
            TokenIntrospectionView,
        ):
            patcher = patch.object(view, "get_client_resolver", return_value=resolver)
            patcher.start()
            self.addCleanup(patcher.stop)

    def authorize(self, redirect_uri=REDIRECT, **data):
        self.client.force_login(self.user)
        params = {
            "response_type": "code",
            "client_id": CLIENT,
            "redirect_uri": redirect_uri,
            "scope": f"{SCOPE_OPENID} {SCOPE_OFFLINE_ACCESS}",
            "state": "state",
            "code_challenge": pkce_s256_challenge(VERIFIER),
            "code_challenge_method": PKCE_METHOD_S256,
        }
        params.update(data)
        return self.client.get(
            reverse("authentik_providers_oauth2:authorize"),
            {key: value for key, value in params.items() if value is not None},
        )

    def planned_params(self) -> OAuthAuthorizationParams:
        """Parameters of the authorization request in the planned flow"""
        return self.client.session[SESSION_KEY_PLAN].context[PLAN_CONTEXT_PARAMS]

    def assert_redirect_error(self, response, error: str, redirect_uri=REDIRECT):
        self.assertEqual(response.status_code, 302)
        url = urlsplit(response.url)
        self.assertEqual(f"{url.scheme}://{url.netloc}{url.path}", redirect_uri)
        self.assertEqual(parse_qs(url.query)["error"], [error])

    def create_code(self, redirect_uri=REDIRECT, **kwargs) -> AuthorizationCode:
        code = AuthorizationCode(
            provider=self.provider,
            user=self.user,
            code=generate_id(),
            auth_time=timezone.now(),
            expires=timezone.now() + timedelta(minutes=1),
            scope=[SCOPE_OPENID, SCOPE_OFFLINE_ACCESS],
            code_challenge=pkce_s256_challenge(VERIFIER),
            code_challenge_method=PKCE_METHOD_S256,
        )
        for key, value in kwargs.items():
            setattr(code, key, value)
        code.bind_client(self.hooked, redirect_uri=redirect_uri, resource=RESOURCE_1)
        code.save()
        return code

    def redeem(self, code: AuthorizationCode, redirect_uri=REDIRECT, **data):
        params = {
            "grant_type": GRANT_TYPE_AUTHORIZATION_CODE,
            "client_id": CLIENT,
            "code": code.code,
            "redirect_uri": redirect_uri,
            "code_verifier": VERIFIER,
        }
        params.update(data)
        return self.client.post(
            reverse("authentik_providers_oauth2:token"),
            {key: value for key, value in params.items() if value is not None},
        )

    def create_token(self, model, client: OAuthClientContext, resource=RESOURCE_1, **kwargs):
        kwargs.setdefault("scope", [SCOPE_OPENID, SCOPE_OFFLINE_ACCESS])
        token = model(
            provider=self.provider,
            user=self.user,
            auth_time=timezone.now(),
            expires=timezone.now() + timedelta(days=30),
            **kwargs,
        )
        token.bind_client(client, resource=resource)
        token.id_token = IDToken.new(self.provider, token, self.factory.get("/"))
        token.save()
        return token

    def basic_auth(self) -> str:
        credentials = f"{self.provider.client_id}:{self.provider.client_secret}"
        return f"Basic {b64encode(credentials.encode()).decode()}"

    # Authorization endpoint

    def test_authorize_redirect_uri_hook(self):
        """The client decides which redirect URIs it may use; the code remembers it"""
        response = self.authorize(REDIRECT_OTHER_PORT)
        self.assertEqual(response.status_code, 302)
        self.assertIn(f"/if/flow/{self.client_flow.slug}/", response.url)
        self.assertEqual(self.planned_params().redirect_uri, REDIRECT_OTHER_PORT)

    def test_authorize_redirect_uri_rejected(self):
        """Redirect URIs the client doesn't allow are never redirected to"""
        response = self.authorize("http://127.0.0.1:1234/other")
        self.assertEqual(response.status_code, 400)
        response = self.authorize(REDIRECT_REGISTERED)
        self.assertEqual(response.status_code, 400)

    def test_authorize_flow_hook(self):
        """The client's authorization flow is planned, not the provider's"""
        response = self.authorize()
        self.assertEqual(response.status_code, 302)
        self.assertIn(f"/if/flow/{self.client_flow.slug}/", response.url)
        plan = self.client.session[SESSION_KEY_PLAN]
        self.assertEqual(plan.flow_pk, self.client_flow.pk.hex)

    def test_authorize_pkce_required(self):
        """The client requires PKCE"""
        response = self.authorize(code_challenge=None, code_challenge_method=None)
        self.assert_redirect_error(response, "invalid_request")

    def test_authorize_pkce_method(self):
        """The client may only use its PKCE methods"""
        response = self.authorize(code_challenge=VERIFIER, code_challenge_method=PKCE_METHOD_PLAIN)
        self.assert_redirect_error(response, "invalid_request")

    def test_authorize_default_resource(self):
        """Without resources, the code is restricted to the client's default resource"""
        response = self.authorize()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.planned_params().resources, (RESOURCE_1,))

    def test_authorize_client_resources(self):
        """Resources are allowed by the client, which may allow fewer than its provider"""
        response = self.authorize(resource=RESOURCE_2)
        self.assertEqual(response.status_code, 302)
        self.assertIn(f"/if/flow/{self.client_flow.slug}/", response.url)
        response = self.authorize(resource=RESOURCE_3)
        self.assert_redirect_error(response, "invalid_target")

    def test_authorize_single_resource(self):
        """The client's grants are restricted to exactly one resource"""
        response = self.authorize(resource=[RESOURCE_1, RESOURCE_2])
        self.assert_redirect_error(response, "invalid_target")

    def test_authorize_resource_missing(self):
        """Without a default resource, a resource must be requested"""
        self.use_client(lambda provider: self.hooked_client(provider, defaults=()))
        response = self.authorize()
        self.assert_redirect_error(response, "invalid_target")
        response = self.authorize(resource=RESOURCE_2)
        self.assertEqual(response.status_code, 302)
        self.assertIn(f"/if/flow/{self.client_flow.slug}/", response.url)

    # Token endpoint

    def test_token_redirect_uri_from_code(self):
        """The code is redeemed with the redirect URI it was issued for, whichever redirect
        URIs the client has at the token endpoint"""
        self.use_client(lambda provider: self.hooked_client(provider, redirect_uris=()))
        code = self.create_code(REDIRECT_OTHER_PORT)
        response = self.redeem(code, REDIRECT)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(loads(response.content)["error"], "invalid_grant")
        response = self.redeem(code, REDIRECT_OTHER_PORT)
        self.assertEqual(response.status_code, 200, response.content)
        access = decode(
            loads(response.content)["access_token"],
            self.keypair.public_key,
            algorithms=["RS256"],
            options={"verify_aud": False},
        )
        self.assertEqual(access["aud"], RESOURCE_1)
        self.assertEqual(access["client_id"], CLIENT)

    def test_token_pkce_required(self):
        """A code issued without PKCE can't be redeemed by a client requiring it"""
        code = self.create_code(code_challenge=None, code_challenge_method=None)
        response = self.redeem(code, code_verifier=None)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(loads(response.content)["error"], "invalid_grant")

    def test_token_pkce_method(self):
        """A code issued with a PKCE method the client may not use can't be redeemed"""
        code = self.create_code(code_challenge=VERIFIER, code_challenge_method=PKCE_METHOD_PLAIN)
        response = self.redeem(code)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(loads(response.content)["error"], "invalid_grant")

    def test_token_resource_from_grant(self):
        """The grant's resource is kept, and can't be swapped for another allowed one"""
        code = self.create_code()
        response = self.redeem(code, resource=RESOURCE_2)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(loads(response.content)["error"], "invalid_target")

    def test_refresh_rotation_hook(self):
        """The client rotates its refresh tokens on every refresh"""
        refresh = self.create_token(RefreshToken, self.hooked, token=generate_id())
        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            {
                "grant_type": GRANT_TYPE_REFRESH_TOKEN,
                "client_id": CLIENT,
                "refresh_token": refresh.token,
                "scope": f"{SCOPE_OPENID} {SCOPE_OFFLINE_ACCESS}",
            },
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertIn("refresh_token", loads(response.content))
        refresh.refresh_from_db()
        self.assertTrue(refresh.revoked)

    def test_refresh_rotation_registered(self):
        """The registered client keeps the provider's threshold"""
        registered = OAuthClientContext.for_provider(self.provider)
        refresh = self.create_token(RefreshToken, registered, resource=None, token=generate_id())
        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            {
                "grant_type": GRANT_TYPE_REFRESH_TOKEN,
                "refresh_token": refresh.token,
                "scope": f"{SCOPE_OPENID} {SCOPE_OFFLINE_ACCESS}",
            },
            HTTP_AUTHORIZATION=self.basic_auth(),
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertNotIn("refresh_token", loads(response.content))

    def test_dpop_htu_endpoint(self):
        """DPoP proofs are bound to the token endpoint the request was made to"""
        request = self.factory.post("/", {"grant_type": GRANT_TYPE_REFRESH_TOKEN})
        request.META["HTTP_DPOP"] = "proof"
        endpoint = "https://authentik.example.com/application/o/app/token/"
        for endpoint_url, expected in (
            (endpoint, endpoint),
            (None, request.build_absolute_uri(reverse("authentik_providers_oauth2:token"))),
        ):
            with (
                self.subTest(endpoint_url=endpoint_url),
                patch(
                    "authentik.providers.oauth2.token.refresh_token.RefreshTokenTokenRequest.parse"
                ),
                patch("authentik.providers.oauth2.token.base.DPoPValidator.validate") as validate,
            ):
                params = parse_token_request(request, self.hooked, "", endpoint_url=endpoint_url)
                params.dpop_proof = "proof"
                params.validate_dpop(request, "jkt")
                self.assertEqual(validate.call_args.kwargs["expected_htu"], expected)

    def test_token_view_endpoint_url(self):
        """The token view passes the endpoint it serves, by default the shared one"""
        with patch(
            "authentik.providers.oauth2.views.token.parse_token_request",
            side_effect=ValueError,
        ) as parse:
            with self.assertRaises(ValueError):
                self.client.post(
                    reverse("authentik_providers_oauth2:token"),
                    {"grant_type": GRANT_TYPE_REFRESH_TOKEN, "client_id": CLIENT},
                )
        self.assertEqual(
            parse.call_args.kwargs["endpoint_url"],
            "http://testserver" + reverse("authentik_providers_oauth2:token"),
        )

    # Revocation and introspection

    def test_revoke_resolver(self):
        """Revocation resolves clients with the view's resolver"""
        token = self.create_token(AccessToken, self.hooked)
        response = self.client.post(
            reverse("authentik_providers_oauth2:token-revoke"),
            {"token": token.token, "client_id": CLIENT},
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(AccessToken.objects.filter(pk=token.pk).exists())

    def introspect(self, token) -> dict:
        response = self.client.post(
            reverse("authentik_providers_oauth2:token-introspection"),
            {"token": token.token},
            HTTP_AUTHORIZATION=self.basic_auth(),
        )
        self.assertEqual(response.status_code, 200)
        return loads(response.content)

    def test_introspect_other_client(self):
        """The provider's registered confidential client introspects access tokens of its
        other clients which are restricted to resources the provider allows"""
        token = self.create_token(AccessToken, self.hooked)
        body = self.introspect(token)
        self.assertTrue(body["active"])
        self.assertEqual(body["client_id"], CLIENT)
        self.assertEqual(body["aud"], RESOURCE_1)

    def test_introspect_other_client_denied(self):
        """...but no other tokens of other clients"""
        cases = {
            "refresh token": self.create_token(RefreshToken, self.hooked, token=generate_id()),
            "no resource": self.create_token(AccessToken, self.hooked, resource=None),
            "resource no longer allowed": self.create_token(
                AccessToken, self.hooked, resource=RESOURCE_2
            ),
        }
        self.provider.allowed_resources = [RESOURCE_1]
        self.provider.save()
        for name, token in cases.items():
            with self.subTest(name):
                self.assertFalse(self.introspect(token)["active"])

    def test_introspect_public_registered_client(self):
        """A public registered client introspects nothing"""
        token = self.create_token(AccessToken, self.hooked)
        self.provider.client_type = ClientType.PUBLIC
        self.provider.save()
        self.assertFalse(self.introspect(token)["active"])

    def test_introspect_resolver(self):
        """Introspection resolves clients with the view's resolver"""
        token = self.create_token(AccessToken, OAuthClientContext.for_provider(self.provider))
        self.assertTrue(self.introspect(token)["active"])

        class NoProvider(ProviderSelector):
            def select(self, request, client_id):
                return None

        with patch.object(
            TokenIntrospectionView,
            "get_client_resolver",
            return_value=OAuthClientResolver(NoProvider()),
        ):
            self.assertFalse(self.introspect(token)["active"])

    # Userinfo

    def test_userinfo_other_client(self):
        """Userinfo only accepts tokens of the provider's registered client"""
        # Both endpoints' scopes, so that only the client is wrong
        hooked = self.create_token(
            AccessToken, self.hooked, scope=[SCOPE_OPENID, SCOPE_GITHUB_USER_EMAIL]
        )
        registered = self.create_token(
            AccessToken, OAuthClientContext.for_provider(self.provider), resource=None
        )
        for url in (
            reverse("authentik_providers_oauth2:userinfo"),
            reverse("authentik_providers_oauth2_root:github-user"),
        ):
            with self.subTest(url=url):
                response = self.client.get(url, HTTP_AUTHORIZATION=f"Bearer {hooked.token}")
                self.assertEqual(response.status_code, 401)
                self.assertIn('error="invalid_token"', response["WWW-Authenticate"])
        response = self.client.get(
            reverse("authentik_providers_oauth2:userinfo"),
            HTTP_AUTHORIZATION=f"Bearer {registered.token}",
        )
        self.assertEqual(response.status_code, 200)

    # Discovery

    def test_provider_info_contributor(self):
        """Registered contributors change the provider's metadata"""

        def contributor(request, provider, info):
            if provider.pk == self.provider.pk:
                info["client_id_metadata_document_supported"] = True
                info["code_challenge_methods_supported"] = [PKCE_METHOD_S256]

        url = reverse(
            "authentik_providers_oauth2:provider-info",
            kwargs={"application_slug": self.app.slug},
        )
        provider_info_contributors.register("test", contributor)
        self.addCleanup(provider_info_contributors.unregister, "test")
        body = loads(self.client.get(url).content)
        self.assertTrue(body["client_id_metadata_document_supported"])
        self.assertEqual(body["code_challenge_methods_supported"], [PKCE_METHOD_S256])
        # Registering again replaces the contributor
        provider_info_contributors.register("test", lambda request, provider, info: None)
        body = loads(self.client.get(url).content)
        self.assertNotIn("client_id_metadata_document_supported", body)
        provider_info_contributors.unregister("test")
        body = loads(self.client.get(url).content)
        self.assertNotIn("client_id_metadata_document_supported", body)


class TestResolveResources(OAuthTestCase):
    """Default resources and the single resource rule"""

    def setUp(self) -> None:
        super().setUp()
        self.provider = OAuth2Provider.objects.create(
            name=generate_id(),
            authorization_flow=None,
            allowed_resources=[RESOURCE_1, RESOURCE_2],
        )
        self.client_context = HookedClientContext(
            provider=self.provider,
            client_id=CLIENT,
            registration_kind="hooked",
            client_type=ClientType.PUBLIC,
            redirect_uris=(),
            grant_types=frozenset(),
            resources=frozenset([RESOURCE_1, RESOURCE_2]),
            defaults=(RESOURCE_1,),
        )

    def assert_error(self, cause: str, *args):
        with self.assertRaises(ResourceIndicatorError) as ctx:
            resolve_resources(*args)
        self.assertEqual(ctx.exception.cause, cause)

    def test_defaults(self):
        client = self.client_context
        self.assertEqual(resolve_resources(client, []), (RESOURCE_1,))
        self.assertEqual(resolve_resources(client, [RESOURCE_2]), (RESOURCE_2,))
        # A grant's resource is kept, never replaced by the default
        self.assertEqual(resolve_resources(client, [], (RESOURCE_2,)), (RESOURCE_2,))

    def test_defaults_not_allowed(self):
        client = replace(self.client_context, defaults=(RESOURCE_3,))
        self.assert_error("resource_not_allowed", client, [])

    def test_single(self):
        client = self.client_context
        self.assert_error("resource_not_single", client, [RESOURCE_1, RESOURCE_2])
        self.assert_error("resource_not_single", client, [], (RESOURCE_1, RESOURCE_2))
        self.assert_error("resource_missing", replace(client, defaults=()), [])
        # Resources are ignored when the client allows none, which leaves none
        self.assert_error(
            "resource_missing", replace(client, resources=frozenset(), defaults=()), [RESOURCE_1]
        )

    def test_join(self):
        self.assertEqual(join_resources(resolve_resources(self.client_context, [])), RESOURCE_1)
