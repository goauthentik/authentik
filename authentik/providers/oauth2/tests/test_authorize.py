"""Test authorize view"""
from django.test import RequestFactory
from django.urls import reverse

from authentik.core.models import Application
from authentik.core.tests.utils import create_test_admin_user, create_test_cert, create_test_flow
from authentik.flows.challenge import ChallengeTypes
from authentik.lib.generators import generate_id, generate_key
from authentik.providers.oauth2.errors import AuthorizeError, ClientIdError, RedirectUriError
from authentik.providers.oauth2.models import (
    AuthorizationCode,
    GrantTypes,
    OAuth2Provider,
    RefreshToken,
)
from authentik.providers.oauth2.tests.utils import OAuthTestCase
from authentik.providers.oauth2.views.authorize import OAuthAuthorizationParams


class TestAuthorize(OAuthTestCase):
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
            request = self.factory.get("/", data={"response_type": "code", "client_id": "invalid"})
            OAuthAuthorizationParams.from_request(request)

    def test_request(self):
        """test request param"""
        OAuth2Provider.objects.create(
            name="test",
            client_id="test",
            authorization_flow=create_test_flow(),
            redirect_uris="http://local.invalid/Foo",
        )
        with self.assertRaises(AuthorizeError):
            request = self.factory.get(
                "/",
                data={
                    "response_type": "code",
                    "client_id": "test",
                    "redirect_uri": "http://local.invalid/Foo",
                    "request": "foo",
                },
            )
            OAuthAuthorizationParams.from_request(request)

    def test_invalid_redirect_uri(self):
        """test missing/invalid redirect URI"""
        OAuth2Provider.objects.create(
            name="test",
            client_id="test",
            authorization_flow=create_test_flow(),
            redirect_uris="http://local.invalid",
        )
        with self.assertRaises(RedirectUriError):
            request = self.factory.get("/", data={"response_type": "code", "client_id": "test"})
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

    def test_invalid_redirect_uri_regex(self):
        """test missing/invalid redirect URI"""
        OAuth2Provider.objects.create(
            name="test",
            client_id="test",
            authorization_flow=create_test_flow(),
            redirect_uris="+",
        )
        with self.assertRaises(RedirectUriError):
            request = self.factory.get("/", data={"response_type": "code", "client_id": "test"})
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

    def test_empty_redirect_uri(self):
        """test empty redirect URI (configure in provider)"""
        OAuth2Provider.objects.create(
            name="test",
            client_id="test",
            authorization_flow=create_test_flow(),
        )
        with self.assertRaises(RedirectUriError):
            request = self.factory.get("/", data={"response_type": "code", "client_id": "test"})
            OAuthAuthorizationParams.from_request(request)
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
            authorization_flow=create_test_flow(),
            redirect_uris="http://local.invalid/Foo",
        )
        request = self.factory.get(
            "/",
            data={
                "response_type": "code",
                "client_id": "test",
                "redirect_uri": "http://local.invalid/Foo",
            },
        )
        self.assertEqual(
            OAuthAuthorizationParams.from_request(request).grant_type,
            GrantTypes.AUTHORIZATION_CODE,
        )
        self.assertEqual(
            OAuthAuthorizationParams.from_request(request).redirect_uri,
            "http://local.invalid/Foo",
        )
        request = self.factory.get(
            "/",
            data={
                "response_type": "id_token",
                "client_id": "test",
                "redirect_uri": "http://local.invalid/Foo",
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
                    "redirect_uri": "http://local.invalid/Foo",
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
                "redirect_uri": "http://local.invalid/Foo",
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
                    "redirect_uri": "http://local.invalid/Foo",
                },
            )
            OAuthAuthorizationParams.from_request(request)

    def test_full_code(self):
        """Test full authorization"""
        flow = create_test_flow()
        provider = OAuth2Provider.objects.create(
            name="test",
            client_id="test",
            authorization_flow=flow,
            redirect_uris="foo://localhost",
        )
        Application.objects.create(name="app", slug="app", provider=provider)
        state = generate_id()
        user = create_test_admin_user()
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
            response.content.decode(),
            {
                "component": "xak-flow-redirect",
                "type": ChallengeTypes.REDIRECT.value,
                "to": f"foo://localhost?code={code.code}&state={state}",
            },
        )

    def test_full_implicit(self):
        """Test full authorization"""
        flow = create_test_flow()
        provider = OAuth2Provider.objects.create(
            name="test",
            client_id="test",
            client_secret=generate_key(),
            authorization_flow=flow,
            redirect_uris="http://localhost",
            signing_key=create_test_cert(),
        )
        Application.objects.create(name="app", slug="app", provider=provider)
        state = generate_id()
        user = create_test_admin_user()
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
            response.content.decode(),
            {
                "component": "xak-flow-redirect",
                "type": ChallengeTypes.REDIRECT.value,
                "to": (
                    f"http://localhost#access_token={token.access_token}"
                    f"&id_token={provider.encode(token.id_token.to_dict())}&token_type=bearer"
                    f"&expires_in=60&state={state}"
                ),
            },
        )
        self.validate_jwt(token, provider)

    def test_full_form_post(self):
        """Test full authorization (form_post response)"""
        flow = create_test_flow()
        provider = OAuth2Provider.objects.create(
            name="test",
            client_id="test",
            client_secret=generate_key(),
            authorization_flow=flow,
            redirect_uris="http://localhost",
            signing_key=create_test_cert(),
        )
        Application.objects.create(name="app", slug="app", provider=provider)
        state = generate_id()
        user = create_test_admin_user()
        self.client.force_login(user)
        # Step 1, initiate params and get redirect to flow
        self.client.get(
            reverse("authentik_providers_oauth2:authorize"),
            data={
                "response_type": "id_token",
                "response_mode": "form_post",
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
            response.content.decode(),
            {
                "component": "ak-stage-autosubmit",
                "type": ChallengeTypes.NATIVE.value,
                "url": "http://localhost",
                "title": "Redirecting to app...",
                "attrs": {
                    "access_token": token.access_token,
                    "id_token": provider.encode(token.id_token.to_dict()),
                    "token_type": "bearer",
                    "expires_in": "60",
                    "state": state,
                },
            },
        )
        self.validate_jwt(token, provider)
