"""Test authorize view"""
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils.encoding import force_str
from jwt import decode

from authentik.core.models import Application, User
from authentik.flows.challenge import ChallengeTypes
from authentik.flows.models import Flow
from authentik.providers.oauth2.errors import (
    AuthorizeError,
    ClientIdError,
    RedirectUriError,
)
from authentik.providers.oauth2.generators import (
    generate_client_id,
    generate_client_secret,
)
from authentik.providers.oauth2.models import (
    AuthorizationCode,
    GrantTypes,
    OAuth2Provider,
    RefreshToken,
)
from authentik.providers.oauth2.views.authorize import OAuthAuthorizationParams


class TestAuthorize(TestCase):
    """Test authorize view"""

    def setUp(self) -> None:
        super().setUp()
        self.factory = RequestFactory()

    def test_invalid_grant_type(self):
        """Test with invalid grant type"""
        with self.assertRaises(AuthorizeError):
            request = self.factory.get("/", data={"response_type": "invalid"})
            OAuthAuthorizationParams.from_request(request)

    def test_invalid_client_id(self):
        """Test invalid client ID"""
        with self.assertRaises(ClientIdError):
            request = self.factory.get(
                "/", data={"response_type": "code", "client_id": "invalid"}
            )
            OAuthAuthorizationParams.from_request(request)

    def test_request(self):
        """test request param"""
        OAuth2Provider.objects.create(
            name="test",
            client_id="test",
            authorization_flow=Flow.objects.first(),
            redirect_uris="http://local.invalid",
        )
        with self.assertRaises(AuthorizeError):
            request = self.factory.get(
                "/",
                data={
                    "response_type": "code",
                    "client_id": "test",
                    "redirect_uri": "http://local.invalid",
                    "request": "foo",
                },
            )
            OAuthAuthorizationParams.from_request(request)

    def test_redirect_uri(self):
        """test missing/invalid redirect URI"""
        OAuth2Provider.objects.create(
            name="test",
            client_id="test",
            authorization_flow=Flow.objects.first(),
            redirect_uris="http://local.invalid",
        )
        with self.assertRaises(RedirectUriError):
            request = self.factory.get(
                "/", data={"response_type": "code", "client_id": "test"}
            )
            OAuthAuthorizationParams.from_request(request)
        with self.assertRaises(RedirectUriError):
            request = self.factory.get(
                "/",
                data={
                    "response_type": "code",
                    "client_id": "test",
                    "redirect_uri": "http://localhost",
                },
            )
            OAuthAuthorizationParams.from_request(request)

    def test_response_type(self):
        """test response_type"""
        OAuth2Provider.objects.create(
            name="test",
            client_id="test",
            authorization_flow=Flow.objects.first(),
            redirect_uris="http://local.invalid",
        )
        request = self.factory.get(
            "/",
            data={
                "response_type": "code",
                "client_id": "test",
                "redirect_uri": "http://local.invalid",
            },
        )
        self.assertEqual(
            OAuthAuthorizationParams.from_request(request).grant_type,
            GrantTypes.AUTHORIZATION_CODE,
        )
        request = self.factory.get(
            "/",
            data={
                "response_type": "id_token",
                "client_id": "test",
                "redirect_uri": "http://local.invalid",
                "scope": "openid",
                "state": "foo",
            },
        )
        self.assertEqual(
            OAuthAuthorizationParams.from_request(request).grant_type,
            GrantTypes.IMPLICIT,
        )
        # Implicit without openid scope
        with self.assertRaises(AuthorizeError):
            request = self.factory.get(
                "/",
                data={
                    "response_type": "id_token",
                    "client_id": "test",
                    "redirect_uri": "http://local.invalid",
                    "state": "foo",
                },
            )
            self.assertEqual(
                OAuthAuthorizationParams.from_request(request).grant_type,
                GrantTypes.IMPLICIT,
            )
        request = self.factory.get(
            "/",
            data={
                "response_type": "code token",
                "client_id": "test",
                "redirect_uri": "http://local.invalid",
                "scope": "openid",
                "state": "foo",
            },
        )
        self.assertEqual(
            OAuthAuthorizationParams.from_request(request).grant_type, GrantTypes.HYBRID
        )
        with self.assertRaises(AuthorizeError):
            request = self.factory.get(
                "/",
                data={
                    "response_type": "invalid",
                    "client_id": "test",
                    "redirect_uri": "http://local.invalid",
                },
            )
            OAuthAuthorizationParams.from_request(request)

    def test_full_code(self):
        """Test full authorization"""
        flow = Flow.objects.create(slug="empty")
        provider = OAuth2Provider.objects.create(
            name="test",
            client_id="test",
            authorization_flow=flow,
            redirect_uris="foo://localhost",
        )
        Application.objects.create(name="app", slug="app", provider=provider)
        state = generate_client_id()
        user = User.objects.get(username="akadmin")
        self.client.force_login(user)
        # Step 1, initiate params and get redirect to flow
        self.client.get(
            reverse("authentik_providers_oauth2:authorize"),
            data={
                "response_type": "code",
                "client_id": "test",
                "state": state,
                "redirect_uri": "foo://localhost",
            },
        )
        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
        )
        code: AuthorizationCode = AuthorizationCode.objects.filter(user=user).first()
        self.assertJSONEqual(
            force_str(response.content),
            {
                "type": ChallengeTypes.REDIRECT.value,
                "to": f"foo://localhost?code={code.code}&state={state}",
            },
        )

    def test_full_implicit(self):
        """Test full authorization"""
        flow = Flow.objects.create(slug="empty")
        provider = OAuth2Provider.objects.create(
            name="test",
            client_id="test",
            client_secret=generate_client_secret(),
            authorization_flow=flow,
            redirect_uris="http://localhost",
        )
        Application.objects.create(name="app", slug="app", provider=provider)
        state = generate_client_id()
        user = User.objects.get(username="akadmin")
        self.client.force_login(user)
        # Step 1, initiate params and get redirect to flow
        self.client.get(
            reverse("authentik_providers_oauth2:authorize"),
            data={
                "response_type": "id_token",
                "client_id": "test",
                "state": state,
                "scope": "openid",
                "redirect_uri": "http://localhost",
            },
        )
        response = self.client.get(
            reverse("authentik_api:flow-executor", kwargs={"flow_slug": flow.slug}),
        )
        token: RefreshToken = RefreshToken.objects.filter(user=user).first()
        self.assertJSONEqual(
            force_str(response.content),
            {
                "type": ChallengeTypes.REDIRECT.value,
                "to": (
                    f"http://localhost#access_token={token.access_token}"
                    f"&id_token={provider.encode(token.id_token.to_dict())}&token_type=bearer"
                    f"&expires_in=600&state={state}"
                ),
            },
        )
        jwt = decode(
            token.access_token,
            provider.client_secret,
            algorithms=[provider.jwt_alg],
            audience=provider.client_id,
        )
        self.assertIsNotNone(jwt["exp"])
        self.assertIsNotNone(jwt["iat"])
        self.assertIsNotNone(jwt["auth_time"])
        self.assertIsNotNone(jwt["acr"])
        self.assertIsNotNone(jwt["sub"])
        self.assertIsNotNone(jwt["iss"])
        # Check id_token
        id_token = token.id_token.to_dict()
        self.assertIsNotNone(id_token["exp"])
        self.assertIsNotNone(id_token["iat"])
        self.assertIsNotNone(id_token["auth_time"])
        self.assertIsNotNone(id_token["acr"])
        self.assertIsNotNone(id_token["sub"])
        self.assertIsNotNone(id_token["iss"])
