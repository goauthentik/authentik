"""Test resource indicators (RFC 8707)"""

from base64 import b64encode
from datetime import timedelta
from json import dumps, loads
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

from django.test import RequestFactory
from django.urls import reverse
from django.utils import timezone
from jwt import decode

from authentik.blueprints.tests import apply_blueprint
from authentik.common.oauth.constants import (
    GRANT_TYPE_AUTHORIZATION_CODE,
    GRANT_TYPE_CLIENT_CREDENTIALS,
    GRANT_TYPE_DEVICE_CODE,
    GRANT_TYPE_REFRESH_TOKEN,
    SCOPE_OFFLINE_ACCESS,
    SCOPE_OPENID,
)
from authentik.core.models import Application
from authentik.core.tests.utils import create_test_admin_user, create_test_flow
from authentik.lib.generators import generate_id
from authentik.policies.expression.models import ExpressionPolicy
from authentik.policies.models import PolicyBinding
from authentik.providers.oauth2.client import (
    LegacyClientAdapter,
    OAuthClientContext,
    OAuthClientResolver,
)
from authentik.providers.oauth2.id_token import IDToken
from authentik.providers.oauth2.models import (
    AccessToken,
    AuthorizationCode,
    ClientType,
    DeviceToken,
    GrantType,
    OAuth2Provider,
    RedirectURI,
    RedirectURIMatchingMode,
    RefreshToken,
    ScopeMapping,
    join_resources,
)
from authentik.providers.oauth2.resources import (
    OAuthResourceResolver,
    ResourceIndicatorError,
    ResourceSource,
    register_resource_source,
    unregister_resource_source,
    validate_resource_indicator,
)
from authentik.providers.oauth2.tests.test_client_bound_grants import (
    CLIENT_A,
    REDIRECT_A,
    FixedSelector,
    SyntheticAdapter,
)
from authentik.providers.oauth2.tests.utils import OAuthTestCase
from authentik.providers.oauth2.views.authorize import AuthorizationFlowInitView
from authentik.providers.oauth2.views.token import TokenView

RESOURCE_1 = "https://mcp.example.com/mcp"
RESOURCE_2 = "https://api.example.com/"
RESOURCE_3 = "https://other.example.com/mcp"


class TestResourceIndicatorValidation(OAuthTestCase):
    """Validation of resource indicators"""

    def test_valid(self):
        """Absolute URIs without a fragment are valid, with or without a query"""
        for value in (
            RESOURCE_1,
            "https://mcp.example.com",
            "https://mcp.example.com:8443/mcp?tenant=1",
            "http://localhost:8000/mcp",
            "urn:example:api",
            "HTTPS://MCP.example.com/mcp",
        ):
            with self.subTest(value=value):
                self.assertEqual(validate_resource_indicator(value), value)

    def test_invalid(self):
        """Relative URIs, fragments, whitespace and non-ASCII characters are refused"""
        for value in (
            "",
            "/mcp",
            "mcp.example.com/mcp",
            "//mcp.example.com/mcp",
            "1https://mcp.example.com",
            "https://mcp.example.com/mcp#fragment",
            "https://mcp.example.com/mcp#",
            "https://",
            "https:///mcp",
            "https://mcp.example.com/a b",
            "https://mcp.example.com/mcp https://other.example.com/mcp",
            "https://mcp.example.com/\n",
            "https://mcp.exämple.com/mcp",
        ):
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_resource_indicator(value)


class TestResourceResolver(OAuthTestCase):
    """Resolving the resources of a request"""

    def setUp(self) -> None:
        super().setUp()
        self.provider = OAuth2Provider.objects.create(
            name=generate_id(),
            authorization_flow=None,
            allowed_resources=[RESOURCE_1, RESOURCE_2],
        )
        self.client_context = OAuthClientContext.for_provider(self.provider)
        self.resolver = OAuthResourceResolver()

    def resolve(self, requested, granted=()):
        return self.resolver.resolve(None, self.client_context, requested, granted)

    def assert_refused(self, cause: str, requested, granted=()):
        with self.assertRaises(ResourceIndicatorError) as ctx:
            self.resolve(requested, granted)
        self.assertEqual(ctx.exception.cause, cause)

    def test_resolve(self):
        """Requested resources must be allowed, and within the grant if it has any"""
        self.assertEqual(self.resolve([]), ())
        self.assertEqual(self.resolve([], (RESOURCE_1,)), (RESOURCE_1,))
        self.assertEqual(self.resolve([RESOURCE_2, RESOURCE_1]), (RESOURCE_2, RESOURCE_1))
        self.assertEqual(self.resolve([RESOURCE_1, RESOURCE_1]), (RESOURCE_1,))
        self.assertEqual(self.resolve([RESOURCE_1], (RESOURCE_1, RESOURCE_2)), (RESOURCE_1,))
        self.assert_refused("resource_not_allowed", [RESOURCE_3])
        self.assert_refused("resource_not_allowed", [RESOURCE_1, RESOURCE_3])
        self.assert_refused("resource_not_granted", [RESOURCE_2], (RESOURCE_1,))
        self.assert_refused("resource_invalid", [f"{RESOURCE_1}#fragment"])
        self.assert_refused("resource_invalid", ["/mcp"])

    def test_exact_match(self):
        """Resources are compared exactly, without normalization"""
        self.assert_refused("resource_not_allowed", [RESOURCE_1 + "/"])
        self.assert_refused("resource_not_allowed", [RESOURCE_1.upper()])

    def test_not_configured(self):
        """Without allowed resources, requested resources are ignored, even malformed ones,
        and a grant's resources are kept"""
        self.provider.allowed_resources = []
        self.provider.save()
        self.assertEqual(self.resolve([RESOURCE_3, "/mcp", "#"]), ())
        self.assertEqual(self.resolve([RESOURCE_2], (RESOURCE_1,)), (RESOURCE_1,))

    def test_sources(self):
        """Sources contribute allowed resources, and registered sources are consulted by
        default, so that components outside core can add resources"""
        calls = []

        class RequestSource(ResourceSource):
            def allowed_resources(self, request, client):
                calls.append(client)
                return [RESOURCE_3]

        source = RequestSource()
        self.assertEqual(
            OAuthResourceResolver([source]).allowed(None, self.client_context),
            frozenset([RESOURCE_3]),
        )
        self.assertNotIn(RESOURCE_3, OAuthResourceResolver().allowed(None, self.client_context))
        register_resource_source(source)
        register_resource_source(source)
        try:
            self.assertEqual(
                OAuthResourceResolver().allowed(None, self.client_context),
                frozenset([RESOURCE_1, RESOURCE_2, RESOURCE_3]),
            )
        finally:
            unregister_resource_source(source)
        self.assertEqual(len(calls), 2)
        self.assertNotIn(RESOURCE_3, OAuthResourceResolver().allowed(None, self.client_context))

    def test_sources_lazy(self):
        """Sources are only consulted when resources are requested"""

        class FailingSource(ResourceSource):
            def allowed_resources(self, request, client):
                raise AssertionError("consulted")

        resolver = OAuthResourceResolver([FailingSource()])
        self.assertEqual(
            resolver.resolve(None, self.client_context, [], (RESOURCE_1,)), (RESOURCE_1,)
        )

    def test_too_long(self):
        """Resources must fit on a grant"""
        long = [f"https://mcp.example.com/{generate_id(500)}" for _ in range(5)]
        self.provider.allowed_resources = long
        self.provider.save()
        self.assert_refused("resource_too_long", long)

    def test_join(self):
        """Grants store resources space-separated"""
        self.assertIsNone(join_resources(()))
        self.assertEqual(join_resources((RESOURCE_1, RESOURCE_2)), f"{RESOURCE_1} {RESOURCE_2}")


class TestResourceIndicators(OAuthTestCase):
    """Resource indicators at the authorization, device authorization and token endpoints"""

    @apply_blueprint("system/providers-oauth2.yaml")
    def setUp(self) -> None:
        super().setUp()
        self.user = create_test_admin_user()
        self.provider = OAuth2Provider.objects.create(
            name=generate_id(),
            authorization_flow=create_test_flow(),
            client_type=ClientType.CONFIDENTIAL,
            grant_types=[
                GrantType.AUTHORIZATION_CODE,
                GrantType.IMPLICIT,
                GrantType.REFRESH_TOKEN,
                GrantType.DEVICE_CODE,
                GrantType.CLIENT_CREDENTIALS,
            ],
            redirect_uris=[RedirectURI(RedirectURIMatchingMode.STRICT, REDIRECT_A)],
            signing_key=self.keypair,
            allowed_resources=[RESOURCE_1, RESOURCE_2],
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
        self.registered = OAuthClientContext.for_provider(self.provider)

    def disable_resources(self):
        self.provider.allowed_resources = []
        self.provider.save()

    def claims(self, token: str) -> dict:
        return decode(
            token,
            self.keypair.public_key,
            algorithms=["RS256"],
            options={"verify_aud": False},
        )

    def authorize(self, resources=(), **data):
        """Authorization request as the registered client"""
        self.client.force_login(self.user)
        params = {
            "response_type": "code",
            "client_id": self.provider.client_id,
            "redirect_uri": REDIRECT_A,
            "scope": f"{SCOPE_OPENID} {SCOPE_OFFLINE_ACCESS}",
            "state": "state",
            "resource": list(resources),
        }
        params.update(data)
        return self.client.get(reverse("authentik_providers_oauth2:authorize"), data=params)

    def token_request(self, resources=(), **data):
        """Token request as the registered client"""
        header = b64encode(
            f"{self.provider.client_id}:{self.provider.client_secret}".encode()
        ).decode()
        data["resource"] = list(resources)
        return self.client.post(
            reverse("authentik_providers_oauth2:token"),
            data,
            HTTP_AUTHORIZATION=f"Basic {header}",
        )

    def create_code(self, resources=()) -> AuthorizationCode:
        code = AuthorizationCode(
            provider=self.provider,
            user=self.user,
            code=generate_id(),
            auth_time=timezone.now(),
            expires=timezone.now() + timedelta(minutes=1),
            scope=[SCOPE_OPENID, SCOPE_OFFLINE_ACCESS],
        )
        code.bind_client(
            self.registered, redirect_uri=REDIRECT_A, resource=join_resources(resources)
        )
        code.save()
        return code

    def create_refresh_token(self, resources=()) -> RefreshToken:
        token = RefreshToken(
            provider=self.provider,
            user=self.user,
            token=generate_id(),
            _id_token=dumps({}),
            auth_time=timezone.now(),
            expires=timezone.now() + timedelta(days=1),
            _scope=f"{SCOPE_OPENID} {SCOPE_OFFLINE_ACCESS}",
        )
        token.bind_client(self.registered, resource=join_resources(resources))
        token.save()
        return token

    def redeem(self, code: AuthorizationCode, resources=()):
        return self.token_request(
            resources,
            grant_type=GRANT_TYPE_AUTHORIZATION_CODE,
            code=code.code,
            redirect_uri=REDIRECT_A,
        )

    def refresh(self, token: RefreshToken, resources=()):
        return self.token_request(
            resources,
            grant_type=GRANT_TYPE_REFRESH_TOKEN,
            refresh_token=token.token,
        )

    def assert_invalid_target(self, response):
        self.assertEqual(response.status_code, 400, response.content)
        self.assertEqual(loads(response.content)["error"], "invalid_target")

    def assert_redirect_error(self, response, error: str):
        self.assertEqual(response.status_code, 302)
        url = urlsplit(response.url)
        self.assertEqual(f"{url.scheme}://{url.netloc}{url.path}", REDIRECT_A)
        query = parse_qs(url.query)
        self.assertEqual(query["error"], [error])
        self.assertEqual(query["state"], ["state"])

    # Authorization endpoint

    def test_authorize_binds_resources(self):
        """Requested resources are recorded on the authorization code"""
        response = self.authorize([RESOURCE_1, RESOURCE_2])
        self.assertEqual(response.status_code, 302)
        code = AuthorizationCode.objects.get(user=self.user)
        self.assertIn(f"code={code.code}", response.url)
        self.assertEqual(code.resources, (RESOURCE_1, RESOURCE_2))

    def test_authorize_without_resource(self):
        """Without resources the code is not restricted to any"""
        self.authorize()
        code = AuthorizationCode.objects.get(user=self.user)
        self.assertIsNone(code.resource)

    def test_authorize_disallowed(self):
        """Resources which aren't allowed are refused with invalid_target"""
        response = self.authorize([RESOURCE_1, RESOURCE_3])
        self.assert_redirect_error(response, "invalid_target")
        self.assertFalse(AuthorizationCode.objects.filter(user=self.user).exists())

    def test_authorize_malformed(self):
        """Malformed resources are refused with invalid_target"""
        for resource in (f"{RESOURCE_1}#fragment", "/mcp", "mcp.example.com"):
            with self.subTest(resource=resource):
                response = self.authorize([resource])
                self.assert_redirect_error(response, "invalid_target")
        self.assertFalse(AuthorizationCode.objects.filter(user=self.user).exists())

    def test_authorize_not_configured(self):
        """Providers without allowed resources ignore the resource parameter"""
        self.disable_resources()
        response = self.authorize([RESOURCE_3, "/mcp"])
        self.assertEqual(response.status_code, 302)
        code = AuthorizationCode.objects.get(user=self.user)
        self.assertIn(f"code={code.code}", response.url)
        self.assertIsNone(code.resource)

    def test_authorize_policy_context(self):
        """Resources are available to application policies"""
        policy = ExpressionPolicy.objects.create(
            name=generate_id(),
            expression=f"return request.context['oauth_resources'] == ['{RESOURCE_1}']",
        )
        PolicyBinding.objects.create(target=self.app, policy=policy, order=0)
        response = self.authorize([RESOURCE_1])
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(REDIRECT_A))
        self.assertTrue(AuthorizationCode.objects.filter(user=self.user).exists())
        AuthorizationCode.objects.filter(user=self.user).delete()
        response = self.authorize([RESOURCE_2])
        self.assertFalse(AuthorizationCode.objects.filter(user=self.user).exists())

    def test_implicit_audience(self):
        """Access tokens issued by the authorization endpoint use the resource as audience"""
        response = self.authorize(
            [RESOURCE_1],
            response_type="id_token token",
            scope=SCOPE_OPENID,
            nonce=generate_id(),
        )
        self.assertEqual(response.status_code, 302)
        fragment = parse_qs(urlsplit(response.url).fragment)
        access = self.claims(fragment["access_token"][0])
        self.assertEqual(access["aud"], RESOURCE_1)
        self.assertEqual(access["client_id"], self.provider.client_id)
        id_token = self.claims(fragment["id_token"][0])
        self.assertEqual(id_token["aud"], self.provider.client_id)
        self.assertEqual(AccessToken.objects.get(user=self.user).resources, (RESOURCE_1,))

    def test_full_flow(self):
        """Authorize for a resource, redeem the code and refresh; every access token is
        restricted to the resource, the ID token to the client"""
        self.authorize([RESOURCE_1])
        code = AuthorizationCode.objects.get(user=self.user)
        response = self.redeem(code, [RESOURCE_1])
        self.assertEqual(response.status_code, 200, response.content)
        body = loads(response.content)
        access = self.claims(body["access_token"])
        self.assertEqual(access["aud"], RESOURCE_1)
        self.assertEqual(access["client_id"], self.provider.client_id)
        self.assertEqual(access["azp"], self.provider.client_id)
        self.assertEqual(self.claims(body["id_token"])["aud"], self.provider.client_id)

        refresh = RefreshToken.objects.get(token=body["refresh_token"])
        response = self.refresh(refresh, [RESOURCE_1])
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(self.claims(loads(response.content)["access_token"])["aud"], RESOURCE_1)

    # Authorization code redemption

    def test_code_default(self):
        """Without resources, tokens are issued for all of the code's resources"""
        code = self.create_code((RESOURCE_1, RESOURCE_2))
        response = self.redeem(code)
        self.assertEqual(response.status_code, 200, response.content)
        body = loads(response.content)
        self.assertEqual(self.claims(body["access_token"])["aud"], [RESOURCE_1, RESOURCE_2])
        refresh = RefreshToken.objects.get(token=body["refresh_token"])
        self.assertEqual(refresh.resources, (RESOURCE_1, RESOURCE_2))

    def test_code_narrow(self):
        """The access token may be narrowed to some of the code's resources; the refresh
        token keeps all of them"""
        code = self.create_code((RESOURCE_1, RESOURCE_2))
        response = self.redeem(code, [RESOURCE_2])
        self.assertEqual(response.status_code, 200, response.content)
        body = loads(response.content)
        self.assertEqual(self.claims(body["access_token"])["aud"], RESOURCE_2)
        self.assertEqual(
            AccessToken.objects.get(token=body["access_token"]).resources, (RESOURCE_2,)
        )
        refresh = RefreshToken.objects.get(token=body["refresh_token"])
        self.assertEqual(refresh.resources, (RESOURCE_1, RESOURCE_2))

    def test_code_widen(self):
        """Resources outside of the code's are refused, even when allowed, and the code
        is not consumed"""
        code = self.create_code((RESOURCE_1,))
        self.assert_invalid_target(self.redeem(code, [RESOURCE_2]))
        self.assert_invalid_target(self.redeem(code, [RESOURCE_1, RESOURCE_2]))
        self.assert_invalid_target(self.redeem(code, [RESOURCE_3]))
        self.assertTrue(AuthorizationCode.objects.filter(pk=code.pk).exists())
        self.assertFalse(AccessToken.objects.filter(user=self.user).exists())

    def test_code_unrestricted(self):
        """A code without resources may be redeemed for any allowed resource"""
        code = self.create_code()
        self.assert_invalid_target(self.redeem(code, [RESOURCE_3]))
        self.assert_invalid_target(self.redeem(code, [f"{RESOURCE_1}#fragment"]))
        response = self.redeem(code, [RESOURCE_1])
        self.assertEqual(response.status_code, 200, response.content)
        body = loads(response.content)
        self.assertEqual(self.claims(body["access_token"])["aud"], RESOURCE_1)
        self.assertIsNone(RefreshToken.objects.get(token=body["refresh_token"]).resource)

    def test_code_not_configured(self):
        """Providers without allowed resources ignore the resource parameter, and issue the
        same tokens as before"""
        self.disable_resources()
        code = self.create_code()
        response = self.redeem(code, [RESOURCE_3, "/mcp"])
        self.assertEqual(response.status_code, 200, response.content)
        body = loads(response.content)
        access = self.claims(body["access_token"])
        self.assertEqual(access["aud"], self.provider.client_id)
        self.assertNotIn("client_id", access)
        self.assertIsNone(AccessToken.objects.get(token=body["access_token"]).resource)

    def test_code_not_configured_keeps_grant(self):
        """A grant restricted to resources stays restricted once resources are no longer
        allowed for its provider"""
        code = self.create_code((RESOURCE_1,))
        self.disable_resources()
        response = self.redeem(code, [RESOURCE_3])
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(self.claims(loads(response.content)["access_token"])["aud"], RESOURCE_1)

    # Refresh tokens

    def test_refresh_narrow(self):
        """Refreshing may narrow the access token to any of the grant's resources, and the
        successor refresh token keeps all of them"""
        token = self.create_refresh_token((RESOURCE_1, RESOURCE_2))
        response = self.refresh(token, [RESOURCE_1])
        self.assertEqual(response.status_code, 200, response.content)
        body = loads(response.content)
        self.assertEqual(self.claims(body["access_token"])["aud"], RESOURCE_1)
        successor = RefreshToken.objects.get(token=body["refresh_token"])
        self.assertEqual(successor.resources, (RESOURCE_1, RESOURCE_2))

        response = self.refresh(successor, [RESOURCE_2])
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(self.claims(loads(response.content)["access_token"])["aud"], RESOURCE_2)

    def test_refresh_default(self):
        """Without resources, refreshed tokens are issued for all of the grant's resources"""
        token = self.create_refresh_token((RESOURCE_1,))
        response = self.refresh(token)
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(self.claims(loads(response.content)["access_token"])["aud"], RESOURCE_1)

    def test_refresh_widen(self):
        """Refreshing never widens the grant, and a refused refresh does not revoke it"""
        token = self.create_refresh_token((RESOURCE_1,))
        self.assert_invalid_target(self.refresh(token, [RESOURCE_2]))
        self.assert_invalid_target(self.refresh(token, [RESOURCE_1, RESOURCE_2]))
        token.refresh_from_db()
        self.assertFalse(token.revoked)

    def test_refresh_no_longer_allowed(self):
        """Resources removed from the allowed resources can no longer be requested"""
        token = self.create_refresh_token((RESOURCE_1, RESOURCE_2))
        self.provider.allowed_resources = [RESOURCE_2]
        self.provider.save()
        self.assert_invalid_target(self.refresh(token, [RESOURCE_1]))
        response = self.refresh(token, [RESOURCE_2])
        self.assertEqual(response.status_code, 200, response.content)

    def test_refresh_not_configured(self):
        """Providers without allowed resources ignore the resource parameter on refresh"""
        self.disable_resources()
        token = self.create_refresh_token()
        response = self.refresh(token, [RESOURCE_3])
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(
            self.claims(loads(response.content)["access_token"])["aud"], self.provider.client_id
        )

    # Device authorization

    def device_authorization(self, resources=()):
        return self.client.post(
            reverse("authentik_providers_oauth2:device"),
            data={
                "client_id": self.provider.client_id,
                "scope": SCOPE_OPENID,
                "resource": list(resources),
            },
        )

    def test_device(self):
        """Device codes are restricted to the requested resources, which the token
        request may narrow but not widen"""
        response = self.device_authorization([RESOURCE_1, RESOURCE_2])
        self.assertEqual(response.status_code, 200, response.content)
        device = DeviceToken.objects.get(device_code=loads(response.content)["device_code"])
        self.assertEqual(device.resources, (RESOURCE_1, RESOURCE_2))
        device.user = self.user
        device.save()

        self.assert_invalid_target(
            self.token_request(
                [RESOURCE_3], grant_type=GRANT_TYPE_DEVICE_CODE, device_code=device.device_code
            )
        )
        response = self.token_request(
            [RESOURCE_2], grant_type=GRANT_TYPE_DEVICE_CODE, device_code=device.device_code
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(self.claims(loads(response.content)["access_token"])["aud"], RESOURCE_2)

    def test_device_disallowed(self):
        """Device authorization refuses resources which aren't allowed"""
        response = self.device_authorization([RESOURCE_3])
        self.assert_invalid_target(response)
        self.assertFalse(DeviceToken.objects.filter(provider=self.provider).exists())

    def test_device_not_configured(self):
        """Providers without allowed resources ignore the resource parameter"""
        self.disable_resources()
        response = self.device_authorization([RESOURCE_3])
        self.assertEqual(response.status_code, 200, response.content)
        device = DeviceToken.objects.get(device_code=loads(response.content)["device_code"])
        self.assertIsNone(device.resource)

    # Client credentials

    def test_client_credentials(self):
        """Client credentials tokens may be requested for allowed resources"""
        response = self.token_request(
            [RESOURCE_1],
            grant_type=GRANT_TYPE_CLIENT_CREDENTIALS,
            scope=SCOPE_OPENID,
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(self.claims(loads(response.content)["access_token"])["aud"], RESOURCE_1)
        self.assert_invalid_target(
            self.token_request(
                [RESOURCE_3], grant_type=GRANT_TYPE_CLIENT_CREDENTIALS, scope=SCOPE_OPENID
            )
        )

    def test_client_credentials_unauthenticated(self):
        """Resources are only checked for authenticated clients"""
        header = b64encode(f"{self.provider.client_id}:{generate_id()}".encode()).decode()
        response = self.client.post(
            reverse("authentik_providers_oauth2:token"),
            {"grant_type": GRANT_TYPE_CLIENT_CREDENTIALS, "resource": RESOURCE_3},
            HTTP_AUTHORIZATION=f"Basic {header}",
        )
        self.assertEqual(response.status_code, 400)
        self.assertNotEqual(loads(response.content)["error"], "invalid_target")

    # Extension points

    def test_registered_source(self):
        """Resources contributed by a registered source can be requested, including ones
        that depend on the request"""
        self.disable_resources()

        class GatewaySource(ResourceSource):
            def allowed_resources(self, request, client):
                return [request.build_absolute_uri("/application/mcp/gateway/")]

        source = GatewaySource()
        register_resource_source(source)
        try:
            self.authorize(["http://testserver/application/mcp/gateway/"])
            code = AuthorizationCode.objects.get(user=self.user)
            self.assertEqual(code.resources, ("http://testserver/application/mcp/gateway/",))
            response = self.redeem(code)
            self.assertEqual(response.status_code, 200, response.content)
            self.assertEqual(
                self.claims(loads(response.content)["access_token"])["aud"],
                "http://testserver/application/mcp/gateway/",
            )
        finally:
            unregister_resource_source(source)

    def test_view_resolver(self):
        """Views may use their own resolver, and resources work for clients other than
        the registered one"""
        self.disable_resources()
        resolver = OAuthResourceResolver([FixedSource([RESOURCE_3])])
        # Selected fresh, as on a real request, so no loaded key ends up in the flow plan
        client_resolver = OAuthClientResolver(
            FixedSelector(OAuth2Provider.objects.get(pk=self.provider.pk)),
            [LegacyClientAdapter(), SyntheticAdapter()],
        )
        self.client.force_login(self.user)
        with (
            patch.object(AuthorizationFlowInitView, "get_resource_resolver", return_value=resolver),
            patch.object(
                AuthorizationFlowInitView, "get_client_resolver", return_value=client_resolver
            ),
        ):
            response = self.client.get(
                reverse("authentik_providers_oauth2:authorize"),
                data={
                    "response_type": "code",
                    "client_id": CLIENT_A,
                    "redirect_uri": REDIRECT_A,
                    "scope": SCOPE_OPENID,
                    "resource": RESOURCE_3,
                },
            )
        self.assertEqual(response.status_code, 302)
        code = AuthorizationCode.objects.get(user=self.user)
        self.assertEqual(code.client_id, CLIENT_A)
        self.assertEqual(code.resources, (RESOURCE_3,))

        with (
            patch.object(TokenView, "get_resource_resolver", return_value=resolver),
            patch.object(TokenView, "get_client_resolver", return_value=client_resolver),
        ):
            response = self.client.post(
                reverse("authentik_providers_oauth2:token"),
                {
                    "grant_type": GRANT_TYPE_AUTHORIZATION_CODE,
                    "client_id": CLIENT_A,
                    "code": code.code,
                    "redirect_uri": REDIRECT_A,
                    "resource": RESOURCE_3,
                },
            )
        self.assertEqual(response.status_code, 200, response.content)
        access = self.claims(loads(response.content)["access_token"])
        self.assertEqual(access["aud"], RESOURCE_3)
        self.assertEqual(access["client_id"], CLIENT_A)
        self.assertEqual(self.claims(loads(response.content)["id_token"])["aud"], CLIENT_A)

    # Introspection and API

    def test_introspection_multiple(self):
        """Introspection reports all resources of an access token as its audience"""
        token = AccessToken(
            provider=self.provider,
            user=self.user,
            auth_time=timezone.now(),
            expires=timezone.now() + timedelta(minutes=5),
            scope=[SCOPE_OPENID],
        )
        token.bind_client(self.registered, resource=join_resources((RESOURCE_1, RESOURCE_2)))
        token.id_token = IDToken.new(self.provider, token, RequestFactory().get("/"))
        token.save()
        header = b64encode(
            f"{self.provider.client_id}:{self.provider.client_secret}".encode()
        ).decode()
        response = self.client.post(
            reverse("authentik_providers_oauth2:token-introspection"),
            data={"token": token.token},
            HTTP_AUTHORIZATION=f"Basic {header}",
        )
        body = loads(response.content)
        self.assertTrue(body["active"])
        self.assertEqual(body["aud"], [RESOURCE_1, RESOURCE_2])

    def test_api_validation(self):
        """Allowed resources must be valid resource indicators"""
        self.client.force_login(self.user)
        url = reverse("authentik_api:oauth2provider-detail", kwargs={"pk": self.provider.pk})
        response = self.client.patch(
            url,
            data={"allowed_resources": [RESOURCE_1, f"{RESOURCE_2}#fragment"]},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("allowed_resources", loads(response.content))
        response = self.client.patch(
            url,
            data={"allowed_resources": [RESOURCE_1, RESOURCE_3, RESOURCE_1]},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.provider.refresh_from_db()
        self.assertEqual(self.provider.allowed_resources, [RESOURCE_1, RESOURCE_3])


class FixedSource(ResourceSource):
    """Allows a fixed list of resources"""

    def __init__(self, resources: list[str]):
        self.resources = resources

    def allowed_resources(self, request, client):
        return self.resources
